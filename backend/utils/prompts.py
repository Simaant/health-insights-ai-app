BASE_PROMPT = (
    "You are a medical assistant. Given the following lab test results and optional wearable data, "
    "identify any abnormal markers and suggest relevant, lifestyle-based health recommendations in bullet points.\n\n"
    "Lab markers:\n{lab_markers}\n"
    "{wearable_section}"
)

def build_prompt(flagged: dict, wearable: dict = None):
    lab_section = "\n".join(
        f"- {k}: {v['value']} {v['unit']} (status: {v['status']})" for k, v in flagged.items()
    )
    wearable_section = f"\nWearable data:\n{wearable}" if wearable else ""
    return BASE_PROMPT.format(lab_markers=lab_section, wearable_section=wearable_section)
