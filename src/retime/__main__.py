import asyncio
import itertools
import json
import re
from aiohttp.client import ClientSession
from datetime import date, timedelta
import typer
import os
import aiohttp

app = typer.Typer()

@app.command("fetch")
def _fetch(from_date: str, to_date: str | None = None):
    from_date_obj = date.fromisoformat(from_date)
    to_date_obj = date.fromisoformat(to_date) if to_date is not None else date.today()
    
    token = os.getenv("BEARER_TOKEN")
    assert token
    
    heartbeats = asyncio.run(fetch(from_date_obj, to_date_obj, token))
    
    with open("hackatime.json", "w") as file:
        json.dump(heartbeats, file)

async def get_heartbeats(http: ClientSession, day: date, token: str):
    async with http.get(
        f"https://waka.hackclub.com/api/compat/wakatime/v1/users/current/heartbeats?date={day.isoformat()}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    ) as response:
        return await response.json()

async def fetch(from_date: date, to_date: date, token: str):
    heartbeats = list()
    
    async with aiohttp.ClientSession() as http:
        while from_date <= to_date:
            print(f"Fetching {from_date}")
            heartbeats.extend((await get_heartbeats(http, from_date, token))['data'])
            from_date += timedelta(days=1)
    
    return heartbeats

@app.command("resend")
def _resend(project_name: str, match_folder: str):
    with open("hackatime.json", "r") as file:
        heartbeats: list[dict] = json.load(file)
    
    modified_heartbeats = []
    
    for heartbeat in heartbeats:
        if heartbeat.get("entity", "").startswith(match_folder):
            new_heartbeat = {
                k: v for k, v in heartbeat.items() if k in {
                    "entity",
                    "branch",
                    "category",
                    "editor",
                    "is_write",
                    "language",
                    "lines",
                    "machine",
                    "operating_system",
                    "project_root_count",
                    "time",
                    "type",
                    "user_agent"
                }
            }
            
            # new_heartbeat["user_agent"] = re.sub(
            #     r"(\([\S]+\))\s",
            #     r"\1 github.com/iamawatermelo/retime ",
            #     heartbeat["user_agent_id"]
            # )
            new_heartbeat["time"] += 2
            new_heartbeat["project"] = project_name
            new_heartbeat["user_agent"] = heartbeat["user_agent_id"]
            new_heartbeat["machine_name"] = heartbeat["machine_name_id"]
            
            modified_heartbeats.append(new_heartbeat)
    
    if len(modified_heartbeats) == 0:
        print("no heartbeats were rewritten")
        return
    
    for entity in {x.get("entity") for x in modified_heartbeats}:
        print(entity)
    
    if input(f"Ok to write {len(modified_heartbeats)} events? [y/N] ").strip() != "y":
        print("Aborted.")
        return
    
    token = os.getenv("BEARER_TOKEN")
    assert token
    
    asyncio.run(write_heartbeats(modified_heartbeats, token))

async def write_heartbeats(heartbeats: list, token: str):
    count = 0
    user_agent = heartbeats[0].get("user_agent")
    
    async with aiohttp.ClientSession() as http:
        for batch in itertools.batched(heartbeats, 50):
            count += len(batch)
            print(f"Sending {len(batch)} events ({count}/{len(heartbeats)})")
            
            async with http.post(
                "https://waka.hackclub.com/api/compat/wakatime/v1/users/current/heartbeats.bulk",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": user_agent
                },
                json=list(batch)
            ) as response:
                response.raise_for_status()

if __name__ == "__main__":
    app()