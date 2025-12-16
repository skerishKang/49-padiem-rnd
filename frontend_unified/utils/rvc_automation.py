import os
import shutil
import yaml
from pathlib import Path
import streamlit as st

def find_latest_model(base_dir: Path):
    """
    Finds the latest .pth file in checkpoints or weights directory.
    """
    search_dirs = [
        base_dir / "checkpoints",
        base_dir / "weights",
        base_dir # Also search root just in case
    ]
    
    pth_files = []
    for d in search_dirs:
        if d.exists():
            pth_files.extend(list(d.glob("*.pth")))
            
    if not pth_files:
        return None
        
    # Sort by modification time, newest first
    pth_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # Filter out dummy or default models if possible (optional)
    # For now, just return the newest one that isn't "dummy.pth" if possible
    for f in pth_files:
        if "dummy" not in f.name.lower():
            return f
            
    return pth_files[0]

def find_index_file(base_dir: Path, model_name: str):
    """
    Finds a corresponding .index file. 
    Often named like 'added_..._modelname.index' or just in the logs folder.
    """
    search_dirs = [
        base_dir / "checkpoints",
        base_dir / "logs",
        base_dir
    ]
    
    index_files = []
    for d in search_dirs:
        if d.exists():
            # Search recursively in logs as it might be in subfolders
            if d.name == "logs":
                index_files.extend(list(d.rglob("*.index")))
            else:
                index_files.extend(list(d.glob("*.index")))
                
    if not index_files:
        return None
        
    # Try to find one that matches the model name
    model_stem = Path(model_name).stem
    for f in index_files:
        if model_stem in f.name:
            return f
            
    # If no name match, return the latest one
    index_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return index_files[0]

def apply_latest_model(rvc_module_dir: str = "modules/voice_conversion_rvc"):
    """
    Finds the latest model and updates settings.yaml.
    """
    base_dir = Path(rvc_module_dir)
    if not base_dir.exists():
        return False, f"RVC 모듈 폴더를 찾을 수 없습니다: {base_dir}"
        
    latest_pth = find_latest_model(base_dir)
    if not latest_pth:
        return False, "학습된 모델(.pth)을 찾을 수 없습니다. RVC WebUI에서 학습을 먼저 진행해주세요."
        
    latest_index = find_index_file(base_dir, latest_pth.name)
    
    # Read template
    template_path = base_dir / "config" / "rvc_template.yaml"
    if not template_path.exists():
        return False, f"설정 템플릿을 찾을 수 없습니다: {template_path}"
        
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # Update config
        # Use relative paths for portability if possible, or absolute
        # Let's use relative to project root if running from root
        # But the config loader in run.py might expect paths relative to CWD or absolute.
        # Let's use forward slashes for consistency
        
        config["checkpoint"] = str(latest_pth).replace("\\", "/")
        if latest_index:
            config["index"] = str(latest_index).replace("\\", "/")
        else:
            config["index"] = None
            
        # Write to settings.yaml
        settings_path = base_dir / "config" / "settings.yaml"
        with open(settings_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
        msg = f"모델 적용 완료!\n- 모델: {latest_pth.name}\n"
        if latest_index:
            msg += f"- 인덱스: {latest_index.name}"
        else:
            msg += "- 인덱스: 없음"
            
        return True, msg
        
    except Exception as e:
        return False, f"설정 파일 업데이트 중 오류 발생: {str(e)}"
