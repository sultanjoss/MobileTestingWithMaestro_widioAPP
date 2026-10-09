import os
import sys
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def safe(value, default="-"):
    if value is None or str(value).strip() == "":
        return default
    return html.escape(str(value))


def format_duration(seconds):
    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return "-"

    minutes = int(seconds // 60)
    remaining = int(seconds % 60)

    if minutes > 0:
        return f"{minutes}m {remaining}s"

    return f"{remaining}s"


def parse_junit(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    testcases = []

    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        suites = root.findall(".//testsuite")

    for suite in suites:
        suite_name = suite.attrib.get("name", "Maestro")

        for testcase in suite.findall("testcase"):
            name = testcase.attrib.get("name", "Unnamed Test")
            class_name = testcase.attrib.get("classname", suite_name)
            duration = testcase.attrib.get("time", "0")

            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped = testcase.find("skipped")

            if failure is not None:
                status = "FAILED"
                message = (
                    failure.attrib.get("message")
                    or failure.text
                    or "Test failed"
                )
            elif error is not None:
                status = "FAILED"
                message = (
                    error.attrib.get("message")
                    or error.text
                    or "Test error"
                )
            elif skipped is not None:
                status = "SKIPPED"
                message = (
                    skipped.attrib.get("message")
                    or skipped.text
                    or "Test skipped"
                )
            else:
                status = "PASSED"
                message = ""

            testcases.append(
                {
                    "name": name,
                    "module": class_name,
                    "status": status,
                    "duration": float(duration or 0),
                    "message": str(message).strip(),
                }
            )

    return testcases


def generate_report(testcases, output_path):
    total = len(testcases)
    passed = sum(1 for t in testcases if t["status"] == "PASSED")
    failed = sum(1 for t in testcases if t["status"] == "FAILED")
    skipped = sum(1 for t in testcases if t["status"] == "SKIPPED")

    duration = sum(t["duration"] for t in testcases)

    pass_rate = (passed / total * 100) if total else 0

    overall_status = "PASSED" if failed == 0 else "FAILED"
    overall_class = "status-pass" if failed == 0 else "status-fail"

    execution_time = datetime.now().strftime("%d %B %Y %H:%M:%S")

    project_name = os.getenv("JOB_NAME", "Mobile Testing with Maestro")
    build_number = os.getenv("BUILD_NUMBER", "-")
    branch = os.getenv("BRANCH_NAME", "develop")
    commit = os.getenv("GIT_COMMIT", "-")
    build_url = os.getenv("BUILD_URL", "-")

    rows = ""

    for index, test in enumerate(testcases, start=1):
        status_class = {
            "PASSED": "badge-pass",
            "FAILED": "badge-fail",
            "SKIPPED": "badge-skip",
        }.get(test["status"], "badge-skip")

        message = safe(test["message"])

        rows += f"""
        <tr>
            <td>{index}</td>
            <td><strong>{safe(test["name"])}</strong></td>
            <td>{safe(test["module"])}</td>
            <td>
                <span class="badge {status_class}">
                    {safe(test["status"])}
                </span>
            </td>
            <td>{format_duration(test["duration"])}</td>
            <td class="message">{message}</td>
        </tr>
        """

    failed_section = ""

    failed_tests = [
        test for test in testcases if test["status"] == "FAILED"
    ]

    if failed_tests:
        cards = ""

        for test in failed_tests:
            cards += f"""
            <div class="failure-card">
                <div class="failure-title">
                    {safe(test["name"])}
                </div>

                <div class="failure-meta">
                    Module: {safe(test["module"])}
                </div>

                <div class="failure-message">
                    {safe(test["message"])}
                </div>
            </div>
            """

        failed_section = f"""
        <section>
            <div class="section-header">
                <h2>Failed Test Analysis</h2>
                <p>Detail kegagalan yang membutuhkan investigasi.</p>
            </div>

            {cards}
        </section>
        """

    conclusion = (
        f"Seluruh {total} automated test berhasil dijalankan tanpa kegagalan."
        if failed == 0
        else
        f"{failed} dari {total} automated test mengalami kegagalan dan membutuhkan investigasi sebelum proses dilanjutkan."
    )

    recommendation = (
        "Build dapat dilanjutkan ke tahap validasi berikutnya berdasarkan hasil automated test ini."
        if failed == 0
        else
        "Lakukan investigasi, perbaikan, dan re-test terhadap test yang gagal sebelum build dipromosikan."
    )

    report = f"""
<!DOCTYPE html>
<html lang="en">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Mobile Automation Test Report</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        Inter,
        Segoe UI,
        Arial,
        sans-serif;

    background: #f5f7fa;
    color: #172033;
}}

.header {{
    background: #102a43;
    color: white;
    padding: 32px 48px;
}}

.header h1 {{
    margin: 0;
    font-size: 28px;
    font-weight: 700;
}}

.header p {{
    margin-top: 8px;
    margin-bottom: 0;
    color: #d9e2ec;
}}

.container {{
    max-width: 1400px;
    margin: auto;
    padding: 32px;
}}

.metadata {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;

    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;

    border: 1px solid #e5e7eb;
}}

.meta-label {{
    font-size: 12px;
    text-transform: uppercase;
    color: #718096;
    margin-bottom: 6px;
}}

.meta-value {{
    font-size: 15px;
    font-weight: 600;
}}

.cards {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}}

.card {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #e5e7eb;
}}

.card-label {{
    font-size: 13px;
    color: #718096;
    margin-bottom: 12px;
}}

.card-value {{
    font-size: 30px;
    font-weight: 700;
}}

.pass {{
    color: #14804a;
}}

.fail {{
    color: #c62828;
}}

.skip {{
    color: #8a6508;
}}

.status-box {{
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 28px;
    border: 1px solid;
}}

.status-pass {{
    background: #edf9f1;
    border-color: #a7d7b8;
}}

.status-fail {{
    background: #fff1f1;
    border-color: #f2b3b3;
}}

.status-title {{
    font-size: 13px;
    text-transform: uppercase;
    color: #667085;
}}

.status-value {{
    margin-top: 6px;
    font-size: 26px;
    font-weight: 700;
}}

.section-header {{
    margin-bottom: 16px;
}}

.section-header h2 {{
    margin-bottom: 4px;
}}

.section-header p {{
    margin-top: 0;
    color: #667085;
}}

section {{
    background: white;
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 28px;
    border: 1px solid #e5e7eb;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th {{
    background: #f8fafc;
    text-align: left;
    padding: 14px;
    font-size: 13px;
    color: #475467;
    border-bottom: 1px solid #e5e7eb;
}}

td {{
    padding: 14px;
    border-bottom: 1px solid #edf0f2;
    font-size: 14px;
    vertical-align: top;
}}

.badge {{
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
}}

.badge-pass {{
    background: #dcfce7;
    color: #166534;
}}

.badge-fail {{
    background: #fee2e2;
    color: #991b1b;
}}

.badge-skip {{
    background: #fef3c7;
    color: #92400e;
}}

.message {{
    max-width: 400px;
    word-break: break-word;
}}

.failure-card {{
    padding: 18px;
    border: 1px solid #f3c2c2;
    background: #fff7f7;
    border-radius: 8px;
    margin-bottom: 14px;
}}

.failure-title {{
    font-weight: 700;
    margin-bottom: 6px;
}}

.failure-meta {{
    font-size: 13px;
    color: #667085;
    margin-bottom: 12px;
}}

.failure-message {{
    font-family: Consolas, monospace;
    font-size: 13px;
}}

.conclusion {{
    line-height: 1.7;
}}

.footer {{
    text-align: center;
    color: #98a2b3;
    font-size: 12px;
    padding: 24px;
}}

@media (max-width: 900px) {{

    .cards {{
        grid-template-columns: repeat(2, 1fr);
    }}

    .metadata {{
        grid-template-columns: repeat(2, 1fr);
    }}

}}

</style>

</head>

<body>

<div class="header">

    <h1>Mobile Automation Test Report</h1>

    <p>
        Maestro · Android · Jenkins Continuous Integration
    </p>

</div>


<div class="container">

    <div class="metadata">

        <div>
            <div class="meta-label">Project</div>
            <div class="meta-value">{safe(project_name)}</div>
        </div>

        <div>
            <div class="meta-label">Environment</div>
            <div class="meta-value">QA / Automation</div>
        </div>

        <div>
            <div class="meta-label">Platform</div>
            <div class="meta-value">Android</div>
        </div>

        <div>
            <div class="meta-label">Framework</div>
            <div class="meta-value">Maestro 2.11.0</div>
        </div>

        <div>
            <div class="meta-label">Jenkins Build</div>
            <div class="meta-value">#{safe(build_number)}</div>
        </div>

        <div>
            <div class="meta-label">Git Branch</div>
            <div class="meta-value">{safe(branch)}</div>
        </div>

        <div>
            <div class="meta-label">Git Commit</div>
            <div class="meta-value">{safe(commit[:8])}</div>
        </div>

        <div>
            <div class="meta-label">Execution Time</div>
            <div class="meta-value">{execution_time}</div>
        </div>

    </div>


    <div class="status-box {overall_class}">

        <div class="status-title">
            Overall Automation Status
        </div>

        <div class="status-value">
            {overall_status}
        </div>

    </div>


    <div class="cards">

        <div class="card">
            <div class="card-label">Total Tests</div>
            <div class="card-value">{total}</div>
        </div>

        <div class="card">
            <div class="card-label">Passed</div>
            <div class="card-value pass">{passed}</div>
        </div>

        <div class="card">
            <div class="card-label">Failed</div>
            <div class="card-value fail">{failed}</div>
        </div>

        <div class="card">
            <div class="card-label">Skipped</div>
            <div class="card-value skip">{skipped}</div>
        </div>

        <div class="card">
            <div class="card-label">Pass Rate</div>
            <div class="card-value">{pass_rate:.1f}%</div>
        </div>

    </div>


    <section>

        <div class="section-header">
            <h2>Execution Summary</h2>
            <p>
                Automated test execution overview.
            </p>
        </div>

        <table>

            <thead>

            <tr>
                <th>#</th>
                <th>Test Case</th>
                <th>Module</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Result Detail</th>
            </tr>

            </thead>

            <tbody>

                {rows}

            </tbody>

        </table>

    </section>


    {failed_section}


    <section>

        <div class="section-header">
            <h2>QA Conclusion</h2>
        </div>

        <div class="conclusion">

            <p>
                <strong>Conclusion:</strong><br>
                {safe(conclusion)}
            </p>

            <p>
                <strong>Recommendation:</strong><br>
                {safe(recommendation)}
            </p>

            <p>
                <strong>Total Execution Duration:</strong><br>
                {format_duration(duration)}
            </p>

        </div>

    </section>


    <div class="footer">

        Generated automatically by
        Maestro Automation Reporting Pipeline

    </div>

</div>

</body>
</html>
"""

    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        report,
        encoding="utf-8"
    )

    print("=" * 60)
    print("Enterprise Maestro Report Generated")
    print("=" * 60)

    print(f"Total      : {total}")
    print(f"Passed     : {passed}")
    print(f"Failed     : {failed}")
    print(f"Skipped    : {skipped}")
    print(f"Pass Rate  : {pass_rate:.1f}%")
    print(f"Output     : {output.resolve()}")

    print("=" * 60)


def main():

    if len(sys.argv) != 3:

        print(
            "Usage:"
            " python generate_report.py "
            "<junit.xml> <output.html>"
        )

        sys.exit(1)

    xml_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(xml_path).exists():

        print(
            f"JUnit file not found: {xml_path}"
        )

        sys.exit(1)

    testcases = parse_junit(xml_path)

    generate_report(
        testcases,
        output_path
    )


if __name__ == "__main__":
    main()