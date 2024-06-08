# labs-gen-ai-experiments
Generative A.I. experiments for the Nava Labs Gates project

## Lightsail Deployments

Deployments of prototypes use AWS Lightsail for easier setup and maintenance, plus drastically lower costs.

To share devops responsibilities and facilitate my outages in June and beyond, all engineers have been given access to [AWS Lightsail web console](https://lightsail.aws.amazon.com/ls/webapp/home/containers) but all the actions that need to be performed are implemented as GitHub Actions:
- [Lightsail service management](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/lightsail-mgmt.yml)
- [Build and deploy Docker image](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/push-image.yml)

Terms:
- `deployment` = defines Docker image(s), environment variables, port, and health check configurations
- `service` = a [Lightsail Container Service](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-container-services.html), not to be confused with [Lightsail Instances](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-instances-virtual-private-servers-in-amazon-lightsail.html).
    - A service can be in the following states: `DISABLED`, `READY` (no deployment), `UPDATING`, `DEPLOYING`, or `RUNNING` (a deployment). These states are checked in `lightsail-mgmt.yml`.
    - A service defines the capacity (`power` x `scale`) that runs the specified deployment. The chosen capacity determines the cost. The capacity can be changed when the service is in the `READY` or `RUNNING` states.

### Updating deployments

When code is updated, a new image is created, along with a new `deployment`, which is then submitted to the service. Use the [Build and deploy Docker image](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/push-image.yml) GitHub Action to build the image and optionally deploy it to the chosen subdomain. The action performs the following:
1. Populates a `.env` file based on a [GitHub Action secret](https://github.com/navapbc/labs-gen-ai-experiments/settings/secrets/actions), such as `DOT_ENV_FILE_CONTENTS` or `DOT_ENV_FILE_CONTENTS_04`. This secret contains API keys, like `LITERAL_API_KEY` and `OPENAI_API_KEY`.
1. Builds the image using the `.env` file.
1. Pushes the image to the Lightsail service corresponding to the chosen `subdomain`.
1. Creates and submits a new deployment using the image name assigned by Lightsail. The deployment is retried several times in case of failure.

This process takes about 15 minutes to complete.

### Addressing failed deployments

Sometimes a deployment fails due to failed healthchecks, which is indicated in the logs as `Took too long`, even after a `Reached a steady state` message.
* Assuming the Docker image functions properly, retrying the deployment will eventually succeed. In the [Build and deploy Docker image](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/push-image.yml) GitHub Action, retry the last deployment quickly by deselecting `Build and push image` and selecting `Deploy built image or last deployment`.
* Increasing the service's `power` decreases the risk of healthcheck failures. Adjust the power by using the [Lightsail service management](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/lightsail-mgmt.yml) GitHub Action. Note that `medium` and higher power options [start at $40/month](https://aws.amazon.com/lightsail/pricing/), though it is charged per time used.
    - Once deployed, test the application. Then visit the `Metrics` tab of the service to assess the CPU and memory needs of the application.
    - Often, the `power` can be decreased after a successful deployment. For the `05-assistive-chatbot` application, `micro` is sufficient but higher power may be desirable for user testing.

### Creating a new service for deployments

Use the [Lightsail service management](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/lightsail-mgmt.yml) GitHub Action to perform the following procedure.  All commands require a `subdomain` except the `status` and `disable_all` commands. Note the `status` command runs at the end of every run to show the state of Lightsail services.

1. Check the list of existing Lightsail (container) services by running `status` using the GitHub Action or checking the [Lightsail web console](https://lightsail.aws.amazon.com/ls/webapp/home/containers).
    - Each service maps to a subdomain of `navalabs.co`. The name of the service uses the syntax: `<subdomain>-svc`.
1. Existing services can be deleted if desired -- run `delete_service` using the GitHub Action.
1. To create a new service or recreate a deleted service, run `create_new` using the GitHub Action with the desired `subdomain` and `power`.

### Maintenance

Use the [Lightsail service management](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/lightsail-mgmt.yml) GitHub Action to perform the any of the following.

- Delete old images (`delete_old_images`) or old services (`delete_service`)
- Disable services if not expected to be used for a long duration (`disable` or `disable_all`)

### Custom domains setup

Setting up custom domains only needs to be done once for a set of subdomains. Ten subdomains of `navalabs.co` were created, and services are automatically configured to use them. To create more subdomains or choose a different set of subdomains, go through this process again.

When a service is created, the service is available via an Amazon-based domain `https://...amazonlightsail.com`. The SSL certificate is associated with this specific Amazon domain.  To associate the service with a custom domain like `chatbot.navalabs.co`, the following was done to use a separate SSL certificate:
- Created a `navalabs.co` DNS Zone at [Domains & DNS](https://lightsail.aws.amazon.com/ls/webapp/home/domains) and copied the 4 provided name servers.
- Since `navalabs.co` is registered at NameCheap, replace the nameservers at NameCheap's website with the Amazon-provided name servers.
- Picked a Lightsail service and in the `Custom domains` tab, selected `Create certificate`, naming the SSL certificate `navalabs-cert` and provided an arbitrary set of subdomains. This certificate is reused by other services.

When the `create_new` command is run using the [Lightsail service management](https://github.com/navapbc/labs-gen-ai-experiments/actions/workflows/lightsail-mgmt.yml) GitHub Action, it:
- creates a new service for the specified `subdomain` using the `navalabs-cert`
- deletes any existing DNS Zone Assignment with the same `subdomain`
- creates a new DNS Zone Assignment for the `subdomain` so that it targets the new service
The effect can be seen in [Lightsail's DNS Zone Assignments](https://lightsail.aws.amazon.com/ls/webapp/domains/navalabs-co/assignments) and the service's `Custom domains` tab.

See [Amazon docs](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-enabling-container-services-custom-domains.html) for details.

#### Targeting EC2 instances

New entries in [Lightsail DNS Zone's DNS records tab](https://lightsail.aws.amazon.com/ls/webapp/domains/navalabs-co/advanced) can be manually created to target applications at other URLs, such as those associated with EC2 instances. This avoids having to use (and pay for) Amazon Cerficate Manager or Route 53.
