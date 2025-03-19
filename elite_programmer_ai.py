import os
import subprocess
import sys
import shutil
import time
import requests
import re
from openai import OpenAI

class MobiusAI:
    """Mobius AI ensures 'Code Fluidity'—self-updating, self-repairing, and fallback protection."""

    def __init__(self, project_name, openai_api_key, deepseek_api_key, output_dir="generated_code", github_repo=None):
        self.project_name = project_name
        self.output_dir = output_dir
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_endpoint = "https://api.deepseek.com/v1/chat/completions"
        self.backup_dir = os.path.join(self.output_dir, "backups")
        self.github_repo = github_repo  # GitHub repo URL (optional)
        self.cache_file = os.path.join(self.output_dir, f"{self.project_name}_update_cache.txt")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_code(self, file_path):
        """Backup before modifying the script."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"{self.project_name}_backup_{timestamp}.py")
        shutil.copy(file_path, backup_path)
        print(f"🛠 Backup created: {backup_path}")

    def check_for_necessary_update(self, file_path):
        """Analyze if an update is actually needed with timeout and caching."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                last_check = f.read().strip()
            if last_check == "NO_UPDATE_NEEDED":
                print("✅ Skipping update check (cached).")
                return None  # Skip checking for updates

        try:
            with open(file_path, "r") as f:
                existing_code = f.read()

            prompt = f"""Analyze the following Python script and compare it against modern best practices,
            latest AI API formats, and security improvements. Only suggest updates if necessary.
            If the script is already optimal, respond with 'NO UPDATE NEEDED'.

            ```python
            {existing_code}
            ```
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are an AI software maintainer."},
                          {"role": "user", "content": prompt}],
                max_tokens=1000,
                timeout=15  # 🕒 Timeout after 15 seconds
            )

            update_suggestion = response.choices[0].message.content.strip()
            if "NO UPDATE NEEDED" in update_suggestion:
                print("✅ Code is already optimal. No update needed.")
                with open(self.cache_file, "w") as f:
                    f.write("NO_UPDATE_NEEDED")  # Cache response to avoid repeat checks
                return None  # No changes required

            return update_suggestion  # Return suggested code changes

        except requests.exceptions.Timeout:
            print("⚠️ OpenAI API took too long. Skipping update check.")
            return None
        except Exception as e:
            print(f"⚠️ Error checking for updates: {e}")
            return None

    def apply_update(self, file_path):
        """Update the script intelligently with validation."""
        update_suggestion = self.check_for_necessary_update(file_path)
        if not update_suggestion:
            return  # Skip if no update is required

        self.backup_code(file_path)  # Create backup before modification

        # Extract clean Python code from AI response
        if "```python" in update_suggestion:
            update_suggestion = update_suggestion.split("```python")[1].split("```")[0].strip()

        with open(file_path, "w") as f:
            f.write(update_suggestion)

        print("✅ Code updated with latest improvements.")

    def execute_code_directly(self, file_path):
        """Run the script and validate output."""
        print("🚀 Running the updated script...")
        try:
            result = subprocess.run([sys.executable, file_path], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Execution Output:\n", result.stdout)
                return True
            else:
                print("❌ Execution Error:\n", result.stderr)
                return False
        except subprocess.TimeoutExpired:
            print("⚠️ Execution took too long and was stopped.")
            return False
        except Exception as e:
            print(f"⚠️ Execution failed: {e}")
            return False

    def rollback(self, file_path):
        """Revert to the last working version in case of failure."""
        backups = sorted(os.listdir(self.backup_dir), reverse=True)
        if not backups:
            print("⚠️ No backup found. Manual intervention needed.")
            return

        latest_backup = os.path.join(self.backup_dir, backups[0])
        shutil.copy(latest_backup, file_path)
        print(f"🔄 Rolled back to last working version: {latest_backup}")

    def build_and_self_improve(self, description):
        """Generate, execute, update, and validate improvements."""
        script_path = os.path.join(self.output_dir, f"{self.project_name}.py")

        # Step 1: Generate Initial Script if Missing
        if not os.path.exists(script_path):
            print("🔹 Generating initial script...")
            self.apply_update(script_path)  # Generates and updates

        # Step 2: Apply Self-Update Logic
        self.apply_update(script_path)  # Ensures it's up-to-date

        # Step 3: Run & Validate
        success = self.execute_code_directly(script_path)
        if not success:
            print("⚠️ Execution failed. Trying self-repair...")
            self.apply_update(script_path)
            success = self.execute_code_directly(script_path)

            if not success:
                print("🚨 Self-repair failed. Rolling back...")
                self.rollback(script_path)
                return False

        print("🎉 Code is up to date and working successfully!")
        return True

if __name__ == "__main__":
    OPENAI_API_KEY = "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"
    DEEPSEEK_API_KEY = "sk-6adbef84071d4848a88e32ef3bfa5a2c"

    mobius = MobiusAI("calculator", OPENAI_API_KEY, DEEPSEEK_API_KEY)
    mobius.build_and_self_improve("A Python calculator script that adds, subtracts, multiplies, and divides two numbers.")
