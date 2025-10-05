#!/usr/bin/env python3
"""
Git项目自动发布脚本
功能：自动更新版本号、提交、打标签、推送到所有远程仓库
"""

import re
import json
import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class GitReleaseManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).absolute()
        self.version_files = {
            'Cargo.toml': self._update_cargo_toml,
            'tauri.conf.json': self._update_tauri_conf,
            'package.json': self._update_package_json,
            'pyproject.toml': self._update_pyproject_toml,
        }

    def run_command(self, cmd: List[str], cwd: Optional[str] = None) -> str:
        """运行命令行命令并返回输出"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"错误执行命令: {' '.join(cmd)}")
            print(f"错误信息: {e.stderr}")
            sys.exit(1)

    def get_current_branch(self) -> str:
        """获取当前分支名"""
        return self.run_command(["git", "branch", "--show-current"])

    def get_remote_repos(self) -> List[str]:
        """获取所有远程仓库名称"""
        output = self.run_command(["git", "remote"])
        return output.split('\n') if output else []

    def check_git_status(self) -> bool:
        """检查git状态，确保工作区干净"""
        status = self.run_command(["git", "status", "--porcelain"])
        return len(status) == 0

    def _update_cargo_toml(self, file_path: Path, new_version: str) -> bool:
        """更新Cargo.toml文件版本号"""
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding='utf-8')
        # 匹配 [package] 部分的 version 字段
        pattern = r'(\[package\]\s*.*?version\s*=\s*")[^"]*(")'
        replacement = r'\g<1>' + new_version + r'\g<2>'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"✓ 更新 {file_path} 版本为 {new_version}")
            return True
        return False

    def _update_tauri_conf(self, file_path: Path, new_version: str) -> bool:
        """更新tauri.conf.json文件版本号"""
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 更新版本号
            if 'package' in config and 'version' in config['package']:
                config['package']['version'] = new_version
                updated = True
            else:
                # 如果package字段不存在，创建它
                if 'package' not in config:
                    config['package'] = {}
                config['package']['version'] = new_version
                updated = True

            if updated:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                print(f"✓ 更新 {file_path} 版本为 {new_version}")
                return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ 解析 {file_path} 失败: {e}")

        return False

    def _update_package_json(self, file_path: Path, new_version: str) -> bool:
        """更新package.json文件版本号"""
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package = json.load(f)

            if 'version' in package:
                package['version'] = new_version
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(package, f, indent=2, ensure_ascii=False)
                print(f"✓ 更新 {file_path} 版本为 {new_version}")
                return True
        except json.JSONDecodeError as e:
            print(f"✗ 解析 {file_path} 失败: {e}")

        return False

    def _update_pyproject_toml(self, file_path: Path, new_version: str) -> bool:
        """更新pyproject.toml文件版本号"""
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding='utf-8')
        # 匹配 [tool.poetry] 或 [project] 部分的 version 字段
        patterns = [
            r'(\[tool\.poetry\]\s*.*?version\s*=\s*")[^"]*(")',
            r'(\[project\]\s*.*?version\s*=\s*")[^"]*(")'
        ]

        for pattern in patterns:
            new_content = re.sub(
                pattern, r'\g<1>' + new_version + r'\g<2>', content, flags=re.DOTALL)
            if new_content != content:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"✓ 更新 {file_path} 版本为 {new_version}")
                return True

        return False

    def update_version_files(self, new_version: str) -> int:
        """更新所有版本文件，返回更新的文件数量"""
        print(f"开始更新版本文件到 {new_version}...")
        updated_count = 0

        for filename, update_func in self.version_files.items():
            file_path = self.project_root / filename
            if update_func(file_path, new_version):
                updated_count += 1

        if updated_count == 0:
            print("⚠ 没有找到需要更新的版本文件")

        return updated_count

    def git_commit_and_tag(self, new_version: str, commit_message: Optional[str] = None) -> None:
        """执行git提交和打标签"""
        if not commit_message:
            commit_message = f"发布版本 v{new_version}"

        # 添加所有更改的文件
        self.run_command(["git", "add", "."])

        # 提交更改
        self.run_command(["git", "commit", "-m", commit_message])
        print(f"✓ 提交更改: {commit_message}")

        # 创建标签
        tag_name = f"v{new_version}"
        self.run_command(
            ["git", "tag", "-a", tag_name, "-m", f"版本 {tag_name}"])
        print(f"✓ 创建标签: {tag_name}")

    def push_to_all_remotes(self, branch: Optional[str] = None) -> None:
        """推送到所有远程仓库"""
        if not branch:
            branch = self.get_current_branch()

        remotes = self.get_remote_repos()
        if not remotes:
            print("⚠ 没有找到远程仓库")
            return

        print(f"开始推送到 {len(remotes)} 个远程仓库...")

        for remote in remotes:
            # 推送分支
            self.run_command(["git", "push", remote, branch])
            print(f"✓ 推送分支到 {remote}/{branch}")

            # 推送标签
            self.run_command(["git", "push", remote, "--tags"])
            print(f"✓ 推送标签到 {remote}")

    def release(self, new_version: str, commit_message: Optional[str] = None,
                branch: Optional[str] = None, skip_push: bool = False) -> None:
        """执行完整的发布流程"""
        print("=" * 50)
        print(f"开始发布流程 - 版本: {new_version}")
        print("=" * 50)

        # 1. 检查工作区状态
        if not self.check_git_status():
            print("✗ 工作区有未提交的更改，请先提交或暂存更改")
            sys.exit(1)
        print("✓ 工作区干净")

        # 2. 更新版本文件
        updated_count = self.update_version_files(new_version)
        if updated_count == 0:
            print("⚠ 没有文件被更新，是否继续？(y/N)")
            if input().lower() != 'y':
                print("发布流程已取消")
                return

        # 3. 提交和打标签
        self.git_commit_and_tag(new_version, commit_message)

        # 4. 推送到所有远程仓库
        if not skip_push:
            self.push_to_all_remotes(branch)
        else:
            print("⚠ 跳过推送步骤")

        print("=" * 50)
        print(f"✅ 发布完成! 版本 {new_version} 已准备就绪")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='Git项目自动发布脚本')
    parser.add_argument('version', help='新版本号 (例如: 1.2.3)')
    parser.add_argument('-m', '--message', help='提交信息')
    parser.add_argument('-b', '--branch', help='目标分支 (默认: 当前分支)')
    parser.add_argument('--skip-push', action='store_true', help='跳过推送步骤')
    parser.add_argument('--project-dir', default='.', help='项目根目录 (默认: 当前目录)')

    args = parser.parse_args()

    # 验证版本号格式 (简单验证)
    if not re.match(r'^\d+\.\d+\.\d+$', args.version):
        print("错误: 版本号格式应为 x.y.z (例如: 1.2.3)")
        sys.exit(1)

    try:
        manager = GitReleaseManager(args.project_dir)
        manager.release(
            new_version=args.version,
            commit_message=args.message,
            branch=args.branch,
            skip_push=args.skip_push
        )
    except Exception as e:
        print(f"发布过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
