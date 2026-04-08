import streamlit as st
from extractor import extract_modules
from utils import estimate_tokens
import json

st.set_page_config(page_title="Context Engine", layout="wide")

CORE_MODULES = {
    "current_objective": "Current Objective",
    "task_state": "Project / Task State",
    "key_decisions": "Key Decisions",
    "constraints": "Constraints",
}

ACCESSORY_MODULES = {
    "instructions": "Instructions",
    "preferences": "Preferences",
    "identity_background": "Identity / Background",
}

ALL_MODULES = {**CORE_MODULES, **ACCESSORY_MODULES}

DEFAULT_PRIVACY = {
    "current_objective": "shareable",
    "task_state": "shareable",
    "key_decisions": "shareable",
    "constraints": "shareable",
    "instructions": "replaceable",
    "preferences": "replaceable",
    "identity_background": "private",
}

PRIORITY_WEIGHT = {
    "current_objective": 5,
    "task_state": 4,
    "key_decisions": 4,
    "constraints": 5,
    "instructions": 2,
    "preferences": 1,
    "identity_background": 1,
}

def build_transfer_prompt(modules, included_map):
    selected_parts = []

    for key, label in ALL_MODULES.items():
        if included_map.get(key, False):
            value = modules.get(key, "").strip()
            if value:
                selected_parts.append(f"[{label}]\n{value}")

    if not selected_parts:
        return "No modules selected."

    body = "\n\n".join(selected_parts)

    return f"""You are continuing an existing workflow. Use the transferred context below.

{body}

Only rely on the included context above. If key information is missing, say so instead of inventing it.
"""

def auto_select_modules(modules, budget, exclude_private=True):
    scored = []

    for key in ALL_MODULES:
        value = modules.get(key, "").strip()
        if not value:
            continue

        privacy = DEFAULT_PRIVACY[key]
        if exclude_private and privacy == "private":
            continue

        token_cost = estimate_tokens(value)
        score = PRIORITY_WEIGHT[key]

        scored.append({
            "key": key,
            "score": score,
            "tokens": token_cost,
            "privacy": privacy,
            "value": value
        })

    scored.sort(key=lambda x: (-x["score"], x["tokens"]))

    included_map = {key: False for key in ALL_MODULES}
    running_total = 0

    for item in scored:
        module_overhead = 8
        projected = running_total + item["tokens"] + module_overhead
        if projected <= budget:
            included_map[item["key"]] = True
            running_total = projected

    return included_map, running_total, scored

def build_modular_packet(modules, included_map):
    packet = []

    for key, label in ALL_MODULES.items():
        value = modules.get(key, "").strip()

        packet.append({
            "module": label,
            "key": key,
            "content": value,
            "included": included_map.get(key, False),
            "privacy": DEFAULT_PRIVACY[key],
            "tokens": estimate_tokens(value)
        })

    return packet

st.title("🧠 Modular Context Abstraction & Transfer Engine")
st.markdown("Extract, structure, and assemble context under constraints.")

# 🔥 INPUT OPTIONS
st.subheader("Input")

# Initialize session state
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# File upload
uploaded_file = st.file_uploader(
    "Upload transcript (.txt or .md)",
    type=["txt", "md"]
)

# If file uploaded → update text
if uploaded_file is not None:
    file_text = uploaded_file.read().decode("utf-8")
    st.session_state.input_text = file_text

# Text area tied to session state
text_input = st.text_area(
    "Or paste transcript here:",
    height=200,
    key="input_text"
)

if "modules" not in st.session_state:
    st.session_state.modules = None

# Extract button
if st.button("Extract Modules"):
    if st.session_state.input_text.strip() == "":
        st.warning("Please provide input.")
    else:
        with st.spinner("Extracting modules..."):
            st.session_state.modules = extract_modules(st.session_state.input_text)

# 🔥 MAIN APP
if st.session_state.modules:
    modules = st.session_state.modules
    st.success("Extraction complete!")

    st.subheader("Assembly Controls")

    assembly_mode = st.radio(
        "Mode:",
        ["Manual", "Auto"],
        horizontal=True
    )

    token_budget = st.slider(
        "Token budget:",
        50, 500, 150
    )

    exclude_private = st.checkbox("Exclude private modules", value=True)

    included_map = {key: False for key in ALL_MODULES}
    auto_selected_keys = set()
    auto_running_total = 0
    auto_ranked = []

    if assembly_mode == "Auto":
        included_map, auto_running_total, auto_ranked = auto_select_modules(
            modules,
            token_budget,
            exclude_private
        )
        auto_selected_keys = {k for k, v in included_map.items() if v}

    left_col, right_col = st.columns([1.3, 1])

    # 🔹 MODULE DISPLAY
    with left_col:
        st.subheader("Modules")

        for key, label in ALL_MODULES.items():
            value = modules.get(key, "")
            tokens = estimate_tokens(value)
            privacy = DEFAULT_PRIVACY[key]

            st.markdown(f"### {label}")

            if assembly_mode == "Manual":
                included_map[key] = st.checkbox(
                    f"Include",
                    value=True if value.strip() else False,
                    key=f"include_{key}"
                )
            else:
                st.checkbox(
                    "Include",
                    value=included_map[key],
                    key=f"auto_{key}",
                    disabled=True
                )

            st.write(value if value.strip() else "_(empty)_")
            st.caption(f"{privacy} | {tokens} tokens")
            st.markdown("---")

    # 🔹 OUTPUT PANEL
    with right_col:

        if assembly_mode == "Auto":
            st.subheader("Auto Selection")
            st.caption(f"Budget: {token_budget} tokens | Used: {auto_running_total}")

            for item in auto_ranked:
                label = ALL_MODULES[item["key"]]
                selected = "✅" if item["key"] in auto_selected_keys else "❌"
                st.write(f"{selected} {label} ({item['tokens']} tokens)")

            st.markdown("---")

        # 🔥 TRANSFER PROMPT
        st.subheader("Transfer Prompt")

        transfer_prompt = build_transfer_prompt(modules, included_map)
        total_tokens = estimate_tokens(transfer_prompt)

        st.text_area("Transfer Prompt Output", value=transfer_prompt, height=250)
        st.caption(f"{total_tokens} tokens")

        st.download_button(
            "Download Prompt",
            transfer_prompt,
            "transfer_prompt.txt"
        )

        # 🔥 BUDGET-AWARE VERSION
        compact_map, _, _ = auto_select_modules(
            modules,
            token_budget,
            exclude_private
        )

        compact_prompt = build_transfer_prompt(modules, compact_map)
        compact_tokens = estimate_tokens(compact_prompt)

        st.subheader("Budget-Aware Prompt")

        st.text_area("Budget-Aware Prompt Output", value=compact_prompt, height=200)
        st.caption(f"{compact_tokens} tokens")

        # 🔥 MODULAR PACKET
        st.subheader("Modular Packet (JSON)")

        packet = build_modular_packet(modules, included_map)

        st.json(packet)

        st.download_button(
            "Download Packet",
            json.dumps(packet, indent=2),
            "modular_packet.json"
        )