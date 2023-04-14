# Arcade Application Update Alerter

Scrapes web sites to check for new versions of apps I use for my arcade cabinet.<br>
Checks MAME, Launchbox, Retroarch, and LedBlinky.  <br>
Sends alert via Pushover on new versions.<br>
Also hosts a web page with a tabole showing current versions and last update timestamp.<br>

Run individual checks with cron<br>
Run webview with systemd service<br>
Add pushover credentials to pushover.creds and save it to /etc<br>
