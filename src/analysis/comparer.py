import datetime
from dataclasses import dataclass, field
from pathlib import Path

from src.models.base import AssetBase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ComparisonResult:
    added: list[AssetBase] = field(default_factory=list)
    removed: list[AssetBase] = field(default_factory=list)
    modified: list[tuple[AssetBase, AssetBase]] = field(default_factory=list)


class CodeComparator:
    """Core comparison logic and HTML report generation."""

    def compare_assets(
        self, base_assets: list[AssetBase], head_assets: list[AssetBase]
    ) -> ComparisonResult:
        base_map = {a.asset_id: a for a in base_assets}
        head_map = {a.asset_id: a for a in head_assets}

        result = ComparisonResult()

        for asset_id, head_asset in head_map.items():
            if asset_id not in base_map:
                result.added.append(head_asset)
            else:
                base_asset = base_map[asset_id]
                if head_asset.sha256 != base_asset.sha256:
                    result.modified.append((base_asset, head_asset))

        for asset_id, base_asset in base_map.items():
            if asset_id not in head_map:
                result.removed.append(base_asset)

        return result

    def generate_html_report(
        self, result: ComparisonResult, info: dict, commits: list[dict] = None
    ) -> Path:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        report_dir = Path("app/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"compare_{file_timestamp}_{info['repo_name']}.html"

        commits_html = ""
        if commits:
            commits_html = f"""
            <h2>Commit Log ({len(commits)} commits)</h2>
            <p>
                Commits present in <b>{info['head_branch']}</b> on {info['repo_name']} but not in
                <b>{info['base_branch']}</b> on {info['repo_name']}.
            </p>
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>Hash</th>
                        <th>Author</th>
                        <th>Date</th>
                        <th>Message</th>
                        <th>Changes</th>
                    </tr>
                </thead>
                <tbody>
            """
            for i, commit in enumerate(commits, 1):
                changes_html = "<br>".join(
                    [f"<b>{c['status']}</b> {c['path']}" for c in commit.get("changes", [])]
                )
                if not changes_html:
                    changes_html = "No file changes detected"

                commits_html += f"""
                    <tr>
                        <td>{i}</td>
                        <td style="font-family: monospace;">{commit['hash']}</td>
                        <td>{commit['author']}</td>
                        <td>{commit['date']}</td>
                        <td>{commit['message']}</td>
                        <td style="font-size: 0.9em;">{changes_html}</td>
                    </tr>
                """
            commits_html += "</tbody></table>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Branch Compare: {info['repo_name']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 2rem;
            color: #333;
            background-color: #f8f9fa;
        }}
        h1, h2 {{ color: #2c3e50; }}
        .card {{
            background: white; padding: 1.5rem; border-radius: 8px;
            border: 1px solid #ddd; margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .metadata p {{ margin: 0.5rem 0; }}
        .summary {{ display: flex; gap: 2rem; margin-bottom: 2rem; }}
        .stat-card {{
            background: #fff;
            padding: 1.5rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            min-width: 150px;
            text-align: center;
            flex: 1;
        }}
        .stat-val {{ font-size: 2rem; font-weight: bold; }}
        .added {{ color: #28a745; }}
        .removed {{ color: #dc3545; }}
        .modified {{ color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #eee; }}
        th {{ background-color: #f1f1f1; font-weight: bold; }}
        tr:hover {{ background-color: #fafafa; }}
        .tag {{
            padding: 4px 8px; border-radius: 12px; font-size: 0.85em;
            color: white; display: inline-block;
        }}
        .tag.bg-added {{ background-color: #28a745; }}
        .tag.bg-removed {{ background-color: #dc3545; }}
        .tag.bg-modified {{ background-color: #ffc107; }}

        /* Floating TOC */
        .toc-container {{
            position: fixed;
            right: 20px;
            top: 20px;
            z-index: 1000;
        }}
        .toc-button {{
            background: #2c3e50;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .toc-content {{
            display: none;
            position: absolute;
            right: 0;
            top: 100%;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            width: 250px;
            margin-top: 10px;
            padding: 10px 0;
            max-height: 80vh;
            overflow-y: auto;
        }}
        .toc-container:hover .toc-content {{ display: block; }}
        .toc-content a {{
            display: block;
            padding: 8px 15px;
            color: #333;
            text-decoration: none;
            border-bottom: 1px solid #eee;
        }}
        .toc-content a:hover {{ background: #f8f9fa; color: #007bff; }}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const tocContent = document.getElementById('toc-links');
        const headers = document.querySelectorAll('h1, h2');
        headers.forEach((header, index) => {{
            if (!header.id) {{
                header.id = 'section-' + index;
            }}
            const link = document.createElement('a');
            link.href = '#' + header.id;
            link.textContent = header.textContent;
            link.style.paddingLeft = header.tagName === 'H2' ? '25px' : '15px';
            tocContent.appendChild(link);
        }});
    }});
    </script>
</head>
<body>
    <div class="toc-container">
        <div class="toc-button">
            <span>&equiv; Table of Contents</span>
        </div>
        <div class="toc-content" id="toc-links"></div>
    </div>

    <h1>Code Comparison Report</h1>

    <div class="card metadata">
        <p><strong>Scenario:</strong> {info.get('scenario', 'Branch vs Branch')}</p>
        <p><strong>{info.get('source_label', 'Base (Source)')}:</strong>
            <b>{info['base_branch']}</b>
            {info.get('source_extra', 'on ' + info.get('repo_name', ''))}
        </p>
        <p><strong>{info.get('target_label', 'Compare (Target)')}:</strong>
            <b>{info['head_branch']}</b>
            {info.get('target_extra', 'on ' + info.get('repo_name', ''))}
        </p>
        {
            "<p><strong>Local Packages:</strong> " + info["local_packages"] + "</p>"
            if info.get("local_packages")
            else ""
        }
        {
            "<p><strong>Local Properties:</strong> " + info["local_properties"] + "</p>"
            if info.get("local_properties")
            else ""
        }
        <p><strong>Date:</strong> {timestamp}</p>
    </div>

    <div class="summary">
        <div class="stat-card">
            <div class="stat-val added">{len(result.added)}</div>
            <div>Added Assets</div>
        </div>
        <div class="stat-card">
            <div class="stat-val removed">{len(result.removed)}</div>
            <div>Removed Assets</div>
        </div>
        <div class="stat-card">
            <div class="stat-val modified">{len(result.modified)}</div>
            <div>Modified Assets</div>
        </div>
    </div>

    <div class="card">
        {commits_html}
    </div>

    <div class="card">
        <h2>Asset Differences</h2>
        <table>
            <thead>
                <tr><th>Status</th><th>Type</th><th>Name</th></tr>
            </thead>
            <tbody>
        """
        for a in result.added:
            html += (
                f"<tr><td><span class='tag bg-added'>Added</span></td>"
                f"<td>{a.asset_type}</td><td>{a.name}</td></tr>"
            )
        for a in result.removed:
            html += (
                f"<tr><td><span class='tag bg-removed'>Removed</span></td>"
                f"<td>{a.asset_type}</td><td>{a.name}</td></tr>"
            )
        for b, _ in result.modified:
            html += (
                f"<tr><td><span class='tag bg-modified'>Modified</span></td>"
                f"<td>{b.asset_type}</td><td>{b.name}</td></tr>"
            )

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        report_file.write_text(html)
        return report_file
