# CrowdSec Custom Bouncer Blocklist Script

This script leverages the CrowdSec Custom Bouncer to export decisions made by your security engine into a blocklist that can then be deployed on your other Security Engines or Firewalls.

# Requirements and Recommendations
* Have the [Custom Bouncer](https://doc.crowdsec.net/u/bouncers/custom) installed.
* Python version ≥ 3.11 (for example, 3.11.2).
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

## Customer Bouncer Configuration: Local API Communication

If you deployed the *custom bouncer* on the same machine as the security engine, API Key configuration is done automatically, and you can move to the next section, otherwise:

[Create an API key for your new bouncer](https://doc.crowdsec.net/u/bouncers/intro) using:
```bash
sudo cscli bouncers add myBouncerName
```

Then, in the bouncer configuration file (usually located at `/etc/crowdsec/bouncers/crowdsec-custom-bouncer.yaml`):
* Fill in the **api_url** and API Key.
  * You can find the API server URL in `/etc/crowdsec/config.yaml`, under `api.server.listen_uri`.
  * In the bouncer config, make sure to prefix the URL with `http://`.


## Custom Bouncer Configuration: Use `push2bl.py` script

* Replace the properties mentioned in this repository's `crowdsec-custom-bouncer.yaml` file:
  * Fill `bin_path` with the path to your venv's python 
  * Replace `bin_args`'s `</path/to/push2bl.py` with the full path to `push2bl.py`
  * Replace `bin_args`'s `<your blocklist name>` with the desired blocklist's name. If it doesn't exist, the script will create it for you.
  * Replace `bin_args`'s  `<your Service API Key>` with your SAPI Key. This can be obtained [from the console](https://doc.crowdsec.net/u/service_api/getting_started).
  * Restrict the `origins` to only `"crowdsec"` and `"cscli"` to ensure only security engine or manually added decisions are included.
* We recommend **not** using a log file, but if you want, you can add the `--log-file` argument followed by an absolute path accessible to the script.
* Ensure `feed_via_stdin` is set to `true` and `total_retries` is set to non-zero value (`10` is the suggested default)

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
