import os
import re
import json
import subprocess
import tempfile
import logging
from functools import partial

import rumps
from cron_descriptor import get_description

logging.basicConfig(
    filename='/tmp/daemon_watch.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DaemonWatchApp(rumps.App):
    def __init__(self):
        logger.debug("Initializing DaemonWatchApp")
        super(DaemonWatchApp, self).__init__("DW")
        self.env = os.environ.copy()
        self.env['PATH'] = '/usr/local/bin:/opt/homebrew/bin:' + \
                           self.env.get('PATH', '')
        
        self.update_timer = rumps.Timer(self.update_data, 60)
        self.update_timer.start()
        logger.debug("Timer started")
        self.update_data(None)
        logger.debug("Initial update_data completed")

    def run_cmd(self, cmd, as_json=False):
        logger.debug(f"Running command: {cmd}")
        try:
            output = subprocess.check_output(
                cmd, text=True, encoding='utf-8', env=self.env, stderr=subprocess.DEVNULL
            )
            return json.loads(output) if as_json else output
        except Exception as e:
            logger.error(f"Command failed: {cmd}, error: {e}")
            return [] if as_json else ""

    def update_data(self, _):
        self.menu.clear()
        
        # 1. Cron Data Fetching
        cron_jobs = self.get_cron_jobs()
        cron_menu = rumps.MenuItem("Cron Schedules")
        if not cron_jobs:
            cron_menu.add(rumps.MenuItem("No jobs found"))
        else:
            for job in cron_jobs:
                status = "🟢" if not job['disabled'] else "⚪️"
                title = f"{status} {job['label']} ({job['human_readable']})"
                job_menu = rumps.MenuItem(title)
                
                # Cron Controls
                toggle_txt = "Enable" if job['disabled'] else "Disable"
                job_menu.add(rumps.MenuItem(
                    toggle_txt,
                    callback=partial(self.toggle_cron, job)
                ))
                job_menu.add(rumps.MenuItem(
                    "Edit Label",
                    callback=partial(self.edit_cron_label, job)
                ))
                schedule_menu = rumps.MenuItem("Edit Schedule")
                schedule_menu.add(rumps.MenuItem("Every N Minutes...", callback=partial(self.edit_schedule_minutes, job)))
                schedule_menu.add(rumps.MenuItem("Every day at N o'clock...", callback=partial(self.edit_schedule_daily, job)))
                schedule_menu.add(rumps.MenuItem("Every N Hours...", callback=partial(self.edit_schedule_hours, job)))
                schedule_menu.add(rumps.MenuItem("Every month on day N...", callback=partial(self.edit_schedule_monthly, job)))
                job_menu.add(schedule_menu)
                job_menu.add(rumps.MenuItem(
                    "Run Now",
                    callback=partial(self.run_cron_now, job)
                ))
                cron_menu.add(job_menu)

        # 2. PM2 Data Fetching
        pm2_procs = self.get_pm2_processes()
        pm2_menu = rumps.MenuItem("PM2 Processes")
        if not pm2_procs:
            pm2_menu.add(rumps.MenuItem("PM2 not found or empty"))
        else:
            for proc in pm2_procs:
                status_icon = "🟢" if proc['status'] == 'online' else "🔴"
                title = (f"{status_icon} {proc['name']} "
                         f"[CPU: {proc['cpu']} | Mem: {proc['memory']}]")
                proc_menu = rumps.MenuItem(title)
                
                # PM2 Controls
                if proc['status'] != 'online':
                    proc_menu.add(rumps.MenuItem(
                        "Start",
                        callback=partial(self.pm2_action, "start", proc['name'])
                    ))
                else:
                    proc_menu.add(rumps.MenuItem(
                        "Restart",
                        callback=partial(self.pm2_action, "restart", proc['name'])
                    ))
                    proc_menu.add(rumps.MenuItem(
                        "Stop",
                        callback=partial(self.pm2_action, "stop", proc['name'])
                    ))
                
                proc_menu.add(rumps.MenuItem(
                    "View Logs",
                    callback=partial(self.pm2_view_logs, proc['name'])
                ))
                pm2_menu.add(proc_menu)

        # 3. Assemble Menu
        self.menu.add(cron_menu)
        self.menu.add(pm2_menu)
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh", callback=self.update_data))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def get_cron_jobs(self):
        output = self.run_cmd(['crontab', '-l'])
        lines = output.splitlines()
        jobs = []
        current_label = None

        cron_regex = r'^(\s*#\s*)?((?:[*/\d,-]+\s+){4}[*/\d,-]+)\s+(.+)$'
        
        for i, line in enumerate(lines):
            label_match = re.match(r'^#\s*NAME:\s*(.+)$', line)
            if label_match:
                current_label = label_match.group(1).strip()
                continue

            match = re.match(cron_regex, line)
            if match:
                is_disabled = bool(match.group(1))
                schedule = match.group(2).strip()
                command = match.group(3).strip()

                try:
                    human_readable = get_description(schedule)
                except Exception:
                    human_readable = schedule

                jobs.append({
                    'line_idx': i,
                    'original_line': line,
                    'label': current_label or command.split()[0],
                    'schedule': schedule,
                    'human_readable': human_readable,
                    'command': command,
                    'disabled': is_disabled
                })
                current_label = None
        return jobs

    def get_pm2_processes(self):
        data = self.run_cmd(['pm2', 'jlist'], as_json=True)
        processes = []
        for proc in data:
            name = proc.get('name')
            status = proc.get('pm2_env', {}).get('status')
            monit = proc.get('monit', {})
            memory = monit.get('memory', 0) / (1024 * 1024)
            cpu = monit.get('cpu', 0)
            processes.append({
                'name': name,
                'status': status,
                'memory': f"{memory:.1f}MB",
                'cpu': f"{cpu}%"
            })
        return processes

    def _write_crontab(self, lines):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        subprocess.run(['crontab', path])
        os.remove(path)
        self.update_data(None)

    def toggle_cron(self, job, _):
        output = self.run_cmd(['crontab', '-l'])
        lines = output.splitlines()
        
        try:
            idx = lines.index(job['original_line'])
        except ValueError:
            return
        
        if job['disabled']:
            lines[idx] = lines[idx].lstrip(" #")
        else:
            lines[idx] = f"# {lines[idx]}"
            
        self._write_crontab(lines)

    def edit_cron_label(self, job, _):
        try:
            logger.debug(f"edit_cron_label clicked for job: {job['label']}")
            window = rumps.Window(
                message="Enter new label for this Cron job:",
                title="Edit Label",
                default_text=job['label'],
                dimensions=(200, 20),
                cancel=True
            )
            response = window.run()
            logger.debug(f"Response clicked: {response.clicked}, text: '{response.text}'")
            if not response.clicked or not response.text.strip():
                logger.debug("Returned early because clicked is False or text is empty.")
                return

            new_label = response.text.strip()
            output = self.run_cmd(['crontab', '-l'])
            lines = output.splitlines()
            
            try:
                idx = lines.index(job['original_line'])
                logger.debug(f"Found original line at idx {idx}")
            except ValueError:
                logger.error("Could not find original_line in current crontab!")
                return

            if idx > 0 and re.match(r'^#\s*NAME:', lines[idx - 1]):
                lines[idx - 1] = f"# NAME: {new_label}"
                logger.debug("Replaced existing label.")
            else:
                lines.insert(idx, f"# NAME: {new_label}")
                logger.debug("Inserted new label.")

            self._write_crontab(lines)
            logger.debug("Called _write_crontab")
        except Exception as e:
            logger.error(f"EXCEPTION in edit_cron_label: {e}", exc_info=True)

    def _prompt_for_integer(self, message, min_val, max_val):
        window = rumps.Window(message=message, title="Edit Schedule", dimensions=(200, 20), cancel=True)
        response = window.run()
        if not response.clicked or not response.text.strip():
            return None
        text = response.text.strip()
        if not text.isdigit():
            rumps.notification("Daemon Watch", "Invalid Input", "Please enter a valid round number.")
            return None
        val = int(text)
        if not (min_val <= val <= max_val):
            rumps.notification("Daemon Watch", "Invalid Value", f"Number must be between {min_val} and {max_val}.")
            return None
        return val

    def _apply_new_schedule(self, job, new_schedule):
        output = self.run_cmd(['crontab', '-l'])
        lines = output.splitlines()
        try:
            idx = lines.index(job['original_line'])
        except ValueError:
            logger.error("Could not find original_line in current crontab!")
            rumps.notification("Daemon Watch", "Error", "Crontab was changed externally.")
            return
        cron_regex = r'^(\s*#\s*)?((?:[*/\d,-]+\s+){4}[*/\d,-]+)\s+(.+)$'
        match = re.match(cron_regex, lines[idx])
        if match:
            prefix = match.group(1) or ""
            command = match.group(3).strip()
            lines[idx] = f"{prefix}{new_schedule} {command}"
            self._write_crontab(lines)
        else:
            logger.error("Regex parsing failed while attempting to update schedule.")
            rumps.notification("Daemon Watch", "Error", "Failed to parse cron schedule.")

    def edit_schedule_minutes(self, job, _):
        val = self._prompt_for_integer("Enter interval in minutes (1~59):", 1, 59)
        if val is not None:
            self._apply_new_schedule(job, f"*/{val} * * * *")

    def edit_schedule_hours(self, job, _):
        val = self._prompt_for_integer("Enter interval in hours (1~23):", 1, 23)
        if val is not None:
            self._apply_new_schedule(job, f"0 */{val} * * *")

    def edit_schedule_daily(self, job, _):
        val = self._prompt_for_integer("Enter specific hour for daily run (0~23):", 0, 23)
        if val is not None:
            self._apply_new_schedule(job, f"0 {val} * * *")

    def edit_schedule_monthly(self, job, _):
        val = self._prompt_for_integer("Enter day of the month (1~31):", 1, 31)
        if val is not None:
            self._apply_new_schedule(job, f"0 0 {val} * *")

    def run_cron_now(self, job, _):
        subprocess.Popen(job['command'], shell=True, env=self.env)
        rumps.notification(
            "Daemon Watch", 
            "Cron Job Triggered", 
            f"Executed: {job['label']}"
        )

    def pm2_action(self, action, name, _):
        subprocess.run(['pm2', action, name], env=self.env)
        self.update_data(None)

    def pm2_view_logs(self, name, _):
        script = f'tell app "Terminal" to do script ' \
                 f'"pm2 logs {name} --lines 10 --nostream"'
        subprocess.run(['osascript', '-e', script])


if __name__ == "__main__":
    DaemonWatchApp().run()
