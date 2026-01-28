import requests


def get_proxy(proxy_type: str, proxy_url: str):
    """
    获取代理
    Args:
        proxy_type: 代理类型，目前支持proxy_pool和ipipgo
        proxy_url: 代理URL，proxy_pool的URL，ipipgo的URL
    Returns:
        proxies: 代理，格式为{"http": "http://proxy", "https": "http://proxy"}，如果获取失败，返回空字典
    """
    if proxy_type == "proxy_pool":
        url = f"{proxy_url}/get"
        res = requests.get(url)
        data = res.json()
        if data.get("code") == 0 and data.get("src") == "no proxy":
            return {}
        proxies = {
            "http": "http://" + data["proxy"],
            "https": "http://" + data["proxy"],
        }
    if proxy_type == "ipipgo":
        proxies = {"http": proxy_url, "https": proxy_url}
    return proxies