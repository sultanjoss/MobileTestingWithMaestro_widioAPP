import os
import sys
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def safe(value, default="-"):
    """Escape values before rendering them into HTML."""
    if value is None or str(value).strip() == "":
        return default
    return html.escape(str(value))


def format_duration(seconds):
    """Convert a duration in seconds to a compact human-readable value."""
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
    """Read Maestro JUnit XML and normalize its test cases."""
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

            try:
                duration = float(testcase.attrib.get("time", "0") or 0)
            except (TypeError, ValueError):
                duration = 0.0

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
                    "duration": duration,
                    "message": str(message).strip(),
                }
            )

    return testcases


def generate_report(testcases, output_path):
    total = len(testcases)
    passed = sum(1 for test in testcases if test["status"] == "PASSED")
    failed = sum(1 for test in testcases if test["status"] == "FAILED")
    skipped = sum(1 for test in testcases if test["status"] == "SKIPPED")

    duration = sum(test["duration"] for test in testcases)
    pass_rate = (passed / total * 100) if total else 0

    # Angles for the CSS donut chart.
    if total > 0:
        passed_degree = (passed / total) * 360
        failed_degree = (failed / total) * 360
    else:
        passed_degree = 0
        failed_degree = 0

    failed_end_degree = passed_degree + failed_degree

    overall_status = "PASSED" if failed == 0 and total > 0 else "FAILED"
    overall_class = "status-pass" if overall_status == "PASSED" else "status-fail"

    execution_time = datetime.now().strftime("%d %B %Y %H:%M:%S")

    # Jenkins metadata. Defaults make the report usable locally too.
    project_name = os.getenv("JOB_NAME", "Mobile Testing with Maestro")
    build_number = os.getenv("BUILD_NUMBER", "-")
    branch = os.getenv("BRANCH_NAME", "develop")
    commit = os.getenv("GIT_COMMIT", "-")
    environment = os.getenv("TEST_ENVIRONMENT", "QA / Automation")
    test_scope = os.getenv("TEST_SCOPE", "Positive Testing")
    device_name = os.getenv("DEVICE_NAME", "Pixel 7 Emulator")
    android_version = os.getenv("ANDROID_VERSION", "Android")
    framework_version = os.getenv("MAESTRO_VERSION", "Maestro 2.11.0")

    rows = ""

    for index, test in enumerate(testcases, start=1):
        status_class = {
            "PASSED": "badge-pass",
            "FAILED": "badge-fail",
            "SKIPPED": "badge-skip",
        }.get(test["status"], "badge-skip")

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
            <td class="message">{safe(test["message"])}</td>
        </tr>
        """

    failed_tests = [
        test for test in testcases if test["status"] == "FAILED"
    ]

    failed_section = ""

    if failed_tests:
        cards = ""

        for test in failed_tests:
            cards += f"""
            <div class="failure-card">
                <div class="failure-title">{safe(test["name"])}</div>
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
                <p>
                    Failure details requiring investigation and re-test.
                </p>
            </div>

            {cards}
        </section>
        """

    if total == 0:
        conclusion = "Tidak ada automated test yang ditemukan pada hasil eksekusi."
        recommendation = "Periksa scope, tag, atau file JUnit sebelum mengambil keputusan build."
        release_recommendation = "RESULT NOT AVAILABLE"
        recommendation_class = "recommendation-warning"
    elif failed == 0:
        conclusion = (
            f"Seluruh {total} automated test berhasil dijalankan "
            "tanpa kegagalan."
        )
        recommendation = (
            "Build dapat dilanjutkan ke tahap validasi berikutnya "
            "berdasarkan hasil automated test ini."
        )
        release_recommendation = "APPROVED FOR NEXT VALIDATION STAGE"
        recommendation_class = "recommendation-pass"
    else:
        conclusion = (
            f"{failed} dari {total} automated test mengalami kegagalan "
            "dan membutuhkan investigasi."
        )
        recommendation = (
            "Lakukan investigasi, perbaikan, dan re-test terhadap test "
            "yang gagal sebelum build dipromosikan."
        )
        release_recommendation = "REQUIRES INVESTIGATION & RE-TEST"
        recommendation_class = "recommendation-fail"

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
    font-family: Inter, "Segoe UI", Arial, sans-serif;
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
    margin: 8px 0 0;
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

.scope-badge {{
    display: inline-block;
    background: #eef4ff;
    color: #3538cd;
    padding: 5px 10px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 700;
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

.analytics-grid {{
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 24px;
    margin-bottom: 28px;
}}

.chart-card,
.executive-card {{
    background: white;
    border-radius: 12px;
    padding: 28px;
    border: 1px solid #e5e7eb;
}}

.section-header {{
    margin-bottom: 16px;
}}

.section-header h2 {{
    margin: 0 0 4px;
    font-size: 21px;
}}

.section-header p {{
    margin: 0;
    color: #667085;
}}

.pie-wrapper {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 18px 0;
}}

.pie-chart {{
    width: 210px;
    height: 210px;
    border-radius: 50%;
    background: conic-gradient(
        #16a34a 0deg {passed_degree:.2f}deg,
        #dc2626 {passed_degree:.2f}deg {failed_end_degree:.2f}deg,
        #d97706 {failed_end_degree:.2f}deg 360deg
    );
    position: relative;
}}

.pie-chart::after {{
    content: "";
    position: absolute;
    width: 125px;
    height: 125px;
    background: white;
    border-radius: 50%;
    top: 42.5px;
    left: 42.5px;
}}

.pie-center {{
    position: absolute;
    z-index: 2;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}

.pie-rate {{
    font-size: 28px;
    font-weight: 700;
}}

.pie-label {{
    font-size: 12px;
    color: #667085;
}}

.legend {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 10px;
    flex-wrap: wrap;
}}

.legend-item {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 13px;
    color: #475467;
}}

.legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
}}

.legend-pass {{
    background: #16a34a;
}}

.legend-fail {{
    background: #dc2626;
}}

.legend-skip {{
    background: #d97706;
}}

.executive-result {{
    font-size: 16px;
    line-height: 1.75;
    color: #344054;
}}

.executive-metrics {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 20px;
}}

.executive-metric {{
    background: #f8fafc;
    border: 1px solid #eaecf0;
    border-radius: 9px;
    padding: 14px;
}}

.executive-metric-label {{
    color: #667085;
    font-size: 12px;
    margin-bottom: 6px;
}}

.executive-metric-value {{
    font-weight: 700;
    font-size: 18px;
}}

.recommendation-box {{
    margin-top: 22px;
    padding: 18px;
    border-radius: 8px;
}}

.recommendation-pass {{
    background: #ecfdf3;
    border-left: 4px solid #16a34a;
}}

.recommendation-fail {{
    background: #fff1f2;
    border-left: 4px solid #dc2626;
}}

.recommendation-warning {{
    background: #fffaeb;
    border-left: 4px solid #d97706;
}}

.recommendation-title {{
    font-size: 12px;
    color: #667085;
    text-transform: uppercase;
    margin-bottom: 5px;
}}

.recommendation-value {{
    font-size: 18px;
    font-weight: 700;
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
    white-space: pre-wrap;
    word-break: break-word;
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

    .analytics-grid {{
        grid-template-columns: 1fr;
    }}

    .executive-metrics {{
        grid-template-columns: 1fr;
    }}

    .header {{
        padding: 26px 24px;
    }}

    .container {{
        padding: 20px;
    }}
}}
</style>
</head>

<body>

<div class="header">
    <h1>Mobile Automation Test Report</h1>
    <p>Maestro · Android · Jenkins Continuous Integration</p>
</div>

<div class="container">

    <div class="metadata">
        <div>
            <div class="meta-label">Project</div>
            <div class="meta-value">{safe(project_name)}</div>
        </div>

        <div>
            <div class="meta-label">Environment</div>
            <div class="meta-value">{safe(environment)}</div>
        </div>

        <div>
            <div class="meta-label">Platform</div>
            <div class="meta-value">Android</div>
        </div>

        <div>
            <div class="meta-label">Framework</div>
            <div class="meta-value">{safe(framework_version)}</div>
        </div>

        <div>
            <div class="meta-label">Test Scope</div>
            <div class="meta-value">
                <span class="scope-badge">{safe(test_scope).upper()}</span>
            </div>
        </div>

        <div>
            <div class="meta-label">Device</div>
            <div class="meta-value">{safe(device_name)}</div>
        </div>

        <div>
            <div class="meta-label">Operating System</div>
            <div class="meta-value">{safe(android_version)}</div>
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
        <div class="status-title">Overall Automation Status</div>
        <div class="status-value">{overall_status}</div>
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

    <div class="analytics-grid">
        <div class="chart-card">
            <div class="section-header">
                <h2>Test Distribution</h2>
                <p>Automation execution result composition.</p>
            </div>

            <div class="pie-wrapper">
                <div class="pie-chart">
                    <div class="pie-center">
                        <div class="pie-rate">{pass_rate:.1f}%</div>
                        <div class="pie-label">Pass Rate</div>
                    </div>
                </div>
            </div>

            <div class="legend">
                <div class="legend-item">
                    <span class="legend-dot legend-pass"></span>
                    Passed ({passed})
                </div>

                <div class="legend-item">
                    <span class="legend-dot legend-fail"></span>
                    Failed ({failed})
                </div>

                <div class="legend-item">
                    <span class="legend-dot legend-skip"></span>
                    Skipped ({skipped})
                </div>
            </div>
        </div>

        <div class="executive-card">
            <div class="section-header">
                <h2>Executive Summary</h2>
                <p>High-level quality assessment of the current build.</p>
            </div>

            <div class="executive-result">
                A total of <strong>{total} automated test cases</strong>
                were executed as part of the
                <strong>{safe(test_scope)}</strong> scope.

                <br><br>

                <strong>{passed}</strong> test cases passed,
                <strong>{failed}</strong> failed, and
                <strong>{skipped}</strong> were skipped.

                The resulting automation pass rate is
                <strong>{pass_rate:.1f}%</strong>.
            </div>

            <div class="executive-metrics">
                <div class="executive-metric">
                    <div class="executive-metric-label">Execution Duration</div>
                    <div class="executive-metric-value">
                        {format_duration(duration)}
                    </div>
                </div>

                <div class="executive-metric">
                    <div class="executive-metric-label">Build</div>
                    <div class="executive-metric-value">
                        #{safe(build_number)}
                    </div>
                </div>

                <div class="executive-metric">
                    <div class="executive-metric-label">Branch</div>
                    <div class="executive-metric-value">
                        {safe(branch)}
                    </div>
                </div>
            </div>

            <div class="recommendation-box {recommendation_class}">
                <div class="recommendation-title">
                    Release Recommendation
                </div>
                <div class="recommendation-value">
                    {release_recommendation}
                </div>
            </div>
        </div>
    </div>

    <section>
        <div class="section-header">
            <h2>Execution Summary</h2>
            <p>Automated test execution overview.</p>
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
        Generated automatically by Maestro Automation Reporting Pipeline
    </div>

</div>

</body>
</html>
"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")

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
            "Usage: python generate_report.py "
            "<junit.xml> <output.html>"
        )
        sys.exit(1)

    xml_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(xml_path).exists():
        print(f"JUnit file not found: {xml_path}")
        sys.exit(1)

    try:
        testcases = parse_junit(xml_path)
        generate_report(testcases, output_path)
    except ET.ParseError as exc:
        print(f"Invalid JUnit XML: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"Report generation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
