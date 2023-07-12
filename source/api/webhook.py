from discord_webhook import DiscordWebhook, DiscordEmbed
import time

def send_content_raw(url, content):
    webhook = DiscordWebhook(url=url, rate_limit_retry=True, content=content)
    webhook.execute()

def send_string_list(url, title, content):
    strings = list()
    string = f"```{title}\n"
    for str in content:
        if len(string)+len(str) >= 1900:
            string += "```"
            strings.append(string)
            string = f"```"
        string += str + "\n"
    string += "```"
    strings.append(string)
    for str in strings:
        webhook = DiscordWebhook(url=url, rate_limit_retry=True, content=str)
        time.sleep(0.5)
        webhook.execute()