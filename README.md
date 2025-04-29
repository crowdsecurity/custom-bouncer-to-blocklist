# CrowdSec Custom Bouncer Blocklist Script

This script leverages the CrowdSec Custom Bouncer to export decisions made by your security engine into a blocklist.

# Requirements and Recommendations
* Have the [Custom Bouncer](https://doc.crowdsec.net/u/bouncers/custom) installed.
* Python version ≥ 3.11 (for example, 3.11.2).
* Use a virtual environment to avoid dependency conflicts.
* Download this repository or the script `push2bl.py` somewhere the Custom Bouncer can access it.
* You'll need a [Service API Key](https://doc.crowdsec.net/u/service_api/getting_started), which is an enterprise feature.

# Step-by-Step Guide

## Deploy the Script
* Download the repository.
* Ensure your Python version is ≥ 3.11.
* Ideally, create a virtual environment to avoid conflicts:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* Install the required packages:
  ```bash
  python3 -m pip install -r requirements.txt
  ```

## Install and Configure the Custom Bouncer
Of course, as usual, [create an API key for your new bouncer](https://doc.crowdsec.net/u/bouncers/intro) using:
```bash
sudo cscli bouncers add myBouncerName
```
Then, in the bouncer configuration file (usually located at `/etc/crowdsec/bouncers/crowdsec-custom-bouncer.yaml`):
* Fill in the **api_url** and API Key.
  * You can find the API server URL in `/etc/crowdsec/config.yaml`, under `api.server.listen_uri`.
  * In the bouncer config, make sure to prefix the URL with `http://`.
* Replace the properties mentioned in this repository's `crowdsec-custom-bouncer.yaml` file:
  * Replace the placeholders (strings inside angle brackets) with your own values.
  * It’s important to restrict the origins to only `"crowdsec"` and `"cscli"` to ensure only security engine or manually added decisions are included.
* We recommend **not** using a log file, but if you want, you can add the `--log-file` argument followed by an absolute path accessible to the script.

Then restart the Bouncer.

## Use the Blocklist
* The blocklist should be visible in the console organization associated with the Service API Key you generated.
* You can download the blocklist to verify in real-time that IPs are being added:
  * Get your blocklist ID:
    * Via the console UI by [filtering for user-made blocklists](https://app.crowdsec.net/blocklists/search?sources=%5B%22custom%22%5D&page=1).
    * Or via the [Get Blocklists API endpoint](https://admin.api.crowdsec.net/v1/docs#/Blocklists/getBlocklists).
  * Download the blocklist content using the [Download endpoint](https://admin.api.crowdsec.net/v1/docs#/Blocklists/downloadBlocklistContent).
* If everything looks good, you can subscribe other Security Engines (SE) or blocklist integrations to this blocklist. **Enjoy!**

# Troubleshooting
* You can set your bouncer to debug mode if nothing happens.  
* If the bouncer exits right after trying to add a decision, it might be because script dependencies are not available — ensure they are installed in the environment where the binary is running.
