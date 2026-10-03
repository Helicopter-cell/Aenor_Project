from flask import Blueprint, render_template

from modules.obsidian_vault import load_obsidian_vault
from services import gemini_service as service

scenario_bp = Blueprint('scenario', __name__)


@scenario_bp.route('/scenario')
def scenario():
    vault_path = service.PROJECT_ROOT / 'data' / 'obsidian_vault'
    graph_data, outline_markdown = load_obsidian_vault(vault_path)
    return render_template(
        'scenario.html',
        graph_data=graph_data,
        outline_markdown=outline_markdown,
    )
