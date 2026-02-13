def filter_output(raw_report: str, filter_keywords: list):
    filtered_results = []
    for line in raw_report.splitlines():
        for kw in filter_keywords:
            if kw.lower() in line.lower():
                filtered_results.append(f"⚠️ {line}")
                break
    return filtered_results
