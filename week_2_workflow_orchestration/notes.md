## Prefect Commands

### Start the server

```bash
prefect server start
```

### Start the agent locally

```bash
prefect agent start --pool "default-agent-pool"
```

### Build a deployment from a flow defined in a Python file

```bash
prefect deployment build parameterized_flow.py:etl_parent_flow -n "Parameterized ETL"
```

This generates a deployment YAML file.

Add the `-a` / `--apply` flag to apply the deployment to the server immediately. 
Otherwise, it can be applied with `prefect deployment apply deployment.yaml`.

#### Build a deployment with a cron schedule

```bash
prefect deployment build parameterized_flow.py:etl_parent_flow -n "Parameterized ETL (Scheduled)" --cron "0 0 * * *"
```

#### Build a deployment with a given infrastructure

This uses a block that should be defined in advance.

```bash
prefect deployment build flows/parameterized_flow.py:etl_parent_flow -n "Parameterized ETL (Scheduled, dockerized)" --cron "0 0 * * *" -ib docker-container/zoom
```

The infrastructure should be passed as `<TYPE>/<NAME>`.

### Run a deployment with parameters

```bash
prefect deployment run "etl-parent-flow/Parameterized ETL (Scheduled, dockerized)" -p "months=[1,2]"
```

## Week 2 Homework

### Question 1. Load January 2020 data

Using the `etl_web_to_gcs.py` flow that loads taxi data into GCS as a guide, create a flow that loads the green taxi CSV dataset for January 2020 into GCS and run it. Look at the logs to find out how many rows the dataset has.

How many rows does that dataset have?

* 447,770
* 766,792
* 299,234
* 822,132

### Solution

Commands:

```bash
docker build -t timovanniedek/prefect:zoom-2-homework .
docker push timovanniedek/prefect:zoom-2-homework
python blocks/make_docker_block.py

prefect deployment build flows/parameterized_flow.py:etl_parent_flow -n "flow-parameterized" -ib docker-container/2-homework-img -a
prefect deployment run "etl-parent-flow/flow-parameterized" -p "months=[1]" -p "year=2020" -p "color=green" -p "clean_data=False"
```

Result:

> Loaded dataframe with 447770 rows


## Question 2. Scheduling with Cron

Cron is a common scheduling specification for workflows. 

Using the flow in `etl_web_to_gcs.py`, create a deployment to run on the first of every month at 5am UTC. What’s the cron schedule for that?

- `0 5 1 * *`
- `0 0 5 1 *`
- `5 * 1 0 *`
- `* * 5 1 0`

Answer:
`0 5 1 * *`

## Question 3. Loading data to BigQuery 

Using `etl_gcs_to_bq.py` as a starting point, modify the script for extracting data from GCS and loading it into BigQuery. This new script should not fill or remove rows with missing values. (The script is really just doing the E and L parts of ETL).

The main flow should print the total number of rows processed by the script. Set the flow decorator to log the print statement.

Parametrize the entrypoint flow to accept a list of months, a year, and a taxi color. 

Make any other necessary changes to the code for it to function as required.

Create a deployment for this flow to run in a local subprocess with local flow code storage (the defaults).

Make sure you have the parquet data files for Yellow taxi data for Feb. 2019 and March 2019 loaded in GCS. Run your deployment to append this data to your BiqQuery table. How many rows did your flow code process?

- 14,851,920
- 12,282,990
- 27,235,753
- 11,338,483

### Solution

Commands:

```bash
prefect deployment build flows/parameterized_flow.py:etl_parent_flow -n "flow-parameterized-local" -a  # the docker image was running out of memory
prefect deployment build flows/etl_gcs_to_bq.py:etl_gcs_to_bq -n "gcs-to-bq" -a
prefect deployment run "etl-parent-flow/flow-parameterized-local" -p "months=[2,3]" -p "year=2019" -p "color=yellow" -p "clean_data=False"
prefect deployment run "etl-gcs-to-bq/gcs-to-bq" -p "months=[2,3]" -p "year=2019" -p "color=yellow"
```

Result:

Number of rows: 7832545
Number of rows: 7019375
Total: 14.851.920

### Question 4. Github Storage Block

Using the `web_to_gcs` script from the videos as a guide, you want to store your flow code in a GitHub repository for collaboration with your team. Prefect can look in the GitHub repo to find your flow code and read it. Create a GitHub storage block from the UI or in Python code and use that in your Deployment instead of storing your flow code locally or baking your flow code into a Docker image. 

Note that you will have to push your code to GitHub, Prefect will not push it for you.

Run your deployment in a local subprocess (the default if you don’t specify an infrastructure). Use the Green taxi data for the month of November 2020.

How many rows were processed by the script?

- 88,019
- 192,297
- 88,605
- 190,225

#### Solution

Git blocks are not recommended to be used. Instead, I am using the prefect deploy command to set up git access for pulling the code from the git remote.

Commands:

```bash
prefect deploy

# Interactive prompt options:
 ? Select a flow to deploy: week_2_workflow_orchestration/homework/flows/parameterized_flow.py
 ? Deployment name (default): web-to-gcs-git-storage 
 ? Would you like to configure a schedule for this deployment? [y/n] (y): n
 ? Looks like you don't have any work pools this flow can be deployed to. Would you like to create one? [y/n] (y): y
 ? What infrastructure type would you like to use for your new work pool?: process
 ? Work pool name: local-work-pool
 ? Your Prefect workers will need access to this flow's code in order to run it. Would you like your workers to pull your flow code from a remote storage location when running this flow? [y/n] (y): y
 ? Please select a remote code storage option. [Use arrows to move; enter to select]: Git Repo
 ? Is git@github.com:TimovNiedek/data-engineering-zoomcamp.git the correct URL to pull your flow code from? [y/n] (y): y
 ? Is week_2 the correct branch to pull your flow code from? [y/n] (y): y
 ? Is this a private repository? [y/n]: n
```

Start the worker:

```bash
prefect worker start --pool 'local-work-pool'
```

Run the deployment:

```bash
prefect deployment run 'etl-parent-flow/web-to-gcs-git-storage' -p "color=green" -p "months=[11]" -p "year=2020"
```

Result:

> Loaded dataframe with 88605 rows

##### Bonus: change code and redeploy



### Question 5. Email or Slack notifications

Q5. It’s often helpful to be notified when something with your dataflow doesn’t work as planned. Choose one of the options below for creating email or slack notifications.

The hosted Prefect Cloud lets you avoid running your own server and has Automations that allow you to get notifications when certain events occur or don’t occur. 

Create a free forever Prefect Cloud account at app.prefect.cloud and connect your workspace to it following the steps in the UI when you sign up. 

Set up an Automation that will send yourself an email when a flow run completes. Run the deployment used in Q4 for the Green taxi data for April 2019. Check your email to see the notification.

Alternatively, use a Prefect Cloud Automation or a self-hosted Orion server Notification to get notifications in a Slack workspace via an incoming webhook. 

Join my temporary Slack workspace with [this link](https://join.slack.com/t/temp-notify/shared_invite/zt-1odklt4wh-hH~b89HN8MjMrPGEaOlxIw). 400 people can use this link and it expires in 90 days. 

In the Prefect Cloud UI create an [Automation](https://docs.prefect.io/ui/automations) or in the Prefect Orion UI create a [Notification](https://docs.prefect.io/ui/notifications/) to send a Slack message when a flow run enters a Completed state. Here is the Webhook URL to use: https://hooks.slack.com/services/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

Test the functionality.

Alternatively, you can grab the webhook URL from your own Slack workspace and Slack App that you create. 


How many rows were processed by the script?

- `125,268`
- `377,922`
- `728,390`
- `514,392`


### Question 6. Secrets

Prefect Secret blocks provide secure, encrypted storage in the database and obfuscation in the UI. Create a secret block in the UI that stores a fake 10-digit password to connect to a third-party service. Once you’ve created your block in the UI, how many characters are shown as asterisks (*) on the next page of the UI?

- 5
- 6
- 8
- 10
