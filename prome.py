from prometheus_api_client import PrometheusConnect
import requests

# prome
prome = PrometheusConnect(url="https://prometheus.peternakclouds.com", disable_ssl=False)

# Discord Webhook URL
discord_webhook_url = "https://discordapp.com/api/webhooks/1323131728809824326/ZQkoloLKNnSTcmJGFedJNYE3ToVVGOyaFu3X3217X2uTOggmxo65g3TQS6-56azT5Eim"

# Parameters for the query
node_id = "ek0bodfpgbpreo2k6mmxogik7"
regex_filter = "/system.slice/docker-.*"

# Check connection
if not prome.check_prometheus_connection():
    print("Failed to connect to Prometheus. Please check the endpoint")
    exit(1)

# Get CPU Usage Per Service
def get_cpu_usage_per_service(node_id, regex_filter):
    query = (
        f"sum(irate(container_cpu_usage_seconds_total{{"
        f"container_label_com_docker_swarm_node_id=~\"{node_id}\", "
        f"id=~\"{regex_filter}\"}}[1m])) "
        f"by (container_label_com_docker_swarm_service_name) * 100"
    )
    return query

# Function to get top 10 services by CPU usage
def get_top10_cpu_usage_per_service(node_id, regex_filter, top_k=10):
    query = (
        f"topk({top_k}, sum(irate(container_cpu_usage_seconds_total{{"
        f"container_label_com_docker_swarm_node_id=~\"{node_id}\", "
        f"id=~\"{regex_filter}\"}}[1m])) "
        f"by (container_label_com_docker_swarm_service_name)) * 100"
    )
    return query

# Function to get memory usage per service
def get_memory_usage_per_service(node_id, regex_filter):
    query = (
        f"sum(container_memory_usage_bytes{{"
        f"container_label_com_docker_swarm_node_id=~\"{node_id}\", "
        f"id=~\"{regex_filter}\"}}) "
        f"by (container_label_com_docker_swarm_service_name)"
    )
    return query

# Function to get top 10 memory usage per service
def get_top10_memory_usage_per_service_with_avg(node_id, regex_filter, interval, top_k=10):
    query = (
        f"topk({top_k}, sort_desc(avg_over_time(container_memory_usage_bytes{{"
        f"container_label_com_docker_swarm_node_id=~\"{node_id}\", "
        f"id=~\"{regex_filter}\"}}[{interval}]))) "
        f"by (container_label_com_docker_swarm_service_name)"
    )
    return query

# Scrape it
def scrape_cpu_usage_per_service(query, description):
    try:
        results = prome.custom_query(query=query)
        print(f"\n{description}")
        output = f"\n**{description}**\n"
        if results:
            for result in results:
                # print(result)
                service_name = result['metric'].get("container_label_com_docker_swarm_service_name", "unknown")
                cpu_usage = float(result["value"][1])
                print(f"Service: {service_name}, CPU Usage: {cpu_usage:.2f}%")
                # output += f"- **Service:** {service_name}, **CPU Usage:** {cpu_usage:.2f}%\n"
                output += f"* Service: {service_name}\n  CPU Usage: {cpu_usage:.2f}%\n"
        else:
            print("No data")
        return output
    except Exception as e:
        print(e)
        print(f"Error while querying: {e}")

# Scrape memory per service
def scrape_memory_usage_per_service(query, description):
    try:
        results = prome.custom_query(query=query)
        print(f"\n{description}")
        output = f"\n**{description}**\n"
        if results:
            for result in results:
                service_name = result['metric'].get("container_label_com_docker_swarm_service_name", "unknown")
                memory_usage = float(result["value"][1]) / (1024 * 1024)  # Convert bytes to MB
                output += f"* Service: {service_name}\n   Memory Usage: {memory_usage:.2f} MB\n"
        else:
            output = "No data available.\n"
        return output
    except Exception as e:
        return f"Error while querying: {e}"

def send_to_discrod(message):
    try:
        payload = {"content": message}
        response = requests.post(discord_webhook_url, json=payload)
        print(payload)
        if response.status_code == 204:
            print("Message sent to Discord successfully!")
        else:
            print(f"Failed to send message to Discord. HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error while sending message to Discord: {e}")

# Generate CPU Usage Queries
cpu_usage = get_cpu_usage_per_service(node_id, regex_filter)
top10_cpu_usage = get_top10_cpu_usage_per_service(node_id, regex_filter)

# Generate Memory Usage Queries
memory_usage = get_memory_usage_per_service(node_id, regex_filter)
top10_memory_usage = get_top10_memory_usage_per_service_with_avg(node_id, regex_filter, interval='15m')

# Get the CPU Usage data
cpu_usage_per_service = scrape_cpu_usage_per_service(cpu_usage, "CPU Usage Per Service")
top10_cpu_usage_per_service = scrape_cpu_usage_per_service(top10_cpu_usage, "Top 10 CPU Usage Per Service")

# Get the Memory Usage data
memory_usage_per_service = scrape_memory_usage_per_service(memory_usage, "Memory Usage Per Service")
top10_memory_usage_per_service = scrape_memory_usage_per_service(top10_memory_usage, "Top 10 Memory Usage Per Service")


send_to_discrod(top10_cpu_usage_per_service)
send_to_discrod(top10_memory_usage_per_service)
