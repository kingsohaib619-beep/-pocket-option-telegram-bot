#################################################################
# Example TEST CMD
#################################################################
# ======================
# python test1.py
# ======================
import time
import logging
import asyncio
from typing import Dict, List, Any, Callable, Optional, Union
from loguru import logger as loguru_logger
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from api_pocket.client import AsyncPocketOptionClient, OrderDirection
from api_pocket.utils import format_timeframe

# Color definitions
ENDC = "[white]"
PURPLE = "[purple]"
DARK_GRAY = "[bright_black]"
OKCYAN = "[steel_blue1]"
lg = "[green3]"
r = "[red]"
dr = "[dark_red]"
dg = "[spring_green4]"
dg2 = "[dark_green]"
bl = "[blue]"
g = "[green]"
w = "[white]"
cy = "[cyan]"
ye = "[yellow]"
yl = "[#FFD700]"
orange = "[dark_orange3]"
Bold_orange = "[bold orange1]"
Bold_green = "[bold green]"

info = g + "[" + w + "i" + g + "]" + ENDC
attempt = g + "[" + w + "+" + g + "]" + ENDC
INPUT = lg + "(" + cy + "~" + lg + ")" + ENDC
sleep = bl + "[" + w + "*" + bl + "]" + ENDC
error = g + "[" + r + "!" + g + "]" + ENDC
success = w + "(" + lg + "*" + w + ")" + ENDC
warning = yl + "(" + w + "!" + yl + ")" + ENDC
wait = yl + "(" + w + "●" + yl + ")" + ENDC
win = w + "[" + lg + "✓" + w + "]" + ENDC
loss = w + "[" + r + "x" + w + "]" + ENDC
draw = w + "[" + OKCYAN + "≈" + w + "]" + ENDC

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(f"log-{time.strftime('%Y-%m-%d')}.txt", encoding="utf-8")]
)
logger = logging.getLogger(__name__)
loguru_logger.remove()
loguru_logger.add(f"log-{time.strftime('%Y-%m-%d')}.txt", level="INFO", encoding="utf-8", backtrace=True, diagnose=True)

#==========================
# Assets Table Display
#==========================
def print_assets_table(assets: Dict[str, Dict[str, Any]], *, only_open: bool = False, sort_by_payout: bool = False, top: int = 0):
    console = Console()
    table = Table(title=f"{PURPLE}Available Assets and Payouts{ENDC}", show_lines=True)
    table.add_column(f"{cy}Symbol{ENDC}", justify="left", no_wrap=True)
    table.add_column(f"{g}Name{ENDC}")
    table.add_column(f"{PURPLE}Type{ENDC}")
    table.add_column(f"{ye}Payout %{ENDC}", justify="right")
    table.add_column(f"{r}OTC{ENDC}")
    table.add_column(f"{ENDC}Open{ENDC}")
    table.add_column(f"{ENDC}Timeframes{ENDC}")
    filtered = {sym: info for sym, info in assets.items() if not only_open or (info.get('is_open') and info.get('payout',0)>0)}
    if not filtered:
        logger.warning(f"{orange}No assets match filter{ENDC}")
        return
    items = sorted(filtered.items(), key=lambda x: x[1].get('payout',0), reverse=sort_by_payout)
    if top>0:
        items = items[:top]
    for sym, info in items:
        tfs_str = ", ".join(format_timeframe(t) for t in info.get('available_timeframes', [])) or "N/A"
        table.add_row(
            f"{cy}{sym}{ENDC}",
            f"{g}{info.get('name','--')}{ENDC}",
            f"{PURPLE}{info.get('type','--')}{ENDC}",
            f"{ye}{info.get('payout','--')}{ENDC}",
            f"{r}Yes{ENDC}" if info.get('is_otc') else f"{ENDC}No{ENDC}",
            f"{g}Yes{ENDC}" if info.get('is_open') else f"{ENDC}No{ENDC}",
            f"{ENDC}{tfs_str}{ENDC}"
        )
    console.print(table)

#==========================
# Candles Table Display
#==========================
def print_candles_table(candles_df, asset: str, timeframe: str):
    console = Console()
    table = Table(title=f"{PURPLE}Candles for {asset} ({timeframe}){ENDC}", show_lines=True)
    table.add_column(f"{cy}Timestamp{ENDC}", justify="left")
    table.add_column(f"{g}Open{ENDC}", justify="right")
    table.add_column(f"{ye}High{ENDC}", justify="right")
    table.add_column(f"{r}Low{ENDC}", justify="right")
    table.add_column(f"{ENDC}Close{ENDC}", justify="right")
    table.add_column(f"{PURPLE}Volume{ENDC}", justify="right")
    for idx,row in candles_df.iterrows():
        table.add_row(
            f"{cy}{idx.strftime('%Y-%m-%d %H:%M:%S')}{ENDC}",
            f"{g}{row['open']:.5f}{ENDC}",
            f"{ye}{row['high']:.5f}{ENDC}",
            f"{r}{row['low']:.5f}{ENDC}",
            f"{ENDC}{row['close']:.5f}{ENDC}",
            f"{PURPLE}{row.get('volume',0):.2f}{ENDC}"
        )
    console.print(table)

#==========================
# Trade Result Panel Display
#==========================
async def check_win_task(client: AsyncPocketOptionClient, order_id: str):
    try:
        profit, status = await client.check_win(order_id)
        if profit is None or status is None:
            rprint(Panel(
                f"{error}{r}No result received for order {order_id}{ENDC}",
                title=f"{r}Trade Result{ENDC}",
                border_style="red"
            ))
            return
        color_code = {
            'win': f"{lg}WIN{ENDC}",
            'loss': f"{r}LOSS{ENDC}",
            'draw': f"{OKCYAN}DRAW{ENDC}"
        }.get(status.lower(), f"{w}{status.upper()}{ENDC}")
        icon = {
            'win': win,
            'loss': loss,
            'draw': draw
        }.get(status.lower(), wait)
        profit_color = g if profit > 0 else r if profit < 0 else OKCYAN
        profit_val = f"{profit_color}${profit:.2f}{ENDC}"

        order_result = await client.check_order_result(order_id)
        completion_time = order_result.expires_at.strftime('%Y-%m-%d %H:%M:%S') if order_result else "N/A"

        panel_content = (
            f"{DARK_GRAY}Order ID: {ye}{order_id}{ENDC}\n"
            f"{DARK_GRAY}Result: {icon} {color_code}\n"
            f"{DARK_GRAY}Profit/Loss: {profit_val}\n"
            f"{DARK_GRAY}Completion Time: {ye}{completion_time}{ENDC}"
        )
        rprint(Panel(
            panel_content,
            title=f"{g}Trade Result{ENDC}",
            border_style="bright_green" if status.lower() == "win" else "red" if status.lower() == "loss" else "yellow"
        ))
    except Exception as e:
        logger.error(f"Failed to check win result for order {order_id}: {e}", exc_info=True)
        rprint(Panel(
            f"{error}Exception occurred: {r}{str(e)}{ENDC}",
            title=f"{r}Trade Result Error{ENDC}",
            border_style="red"
        ))

#==========================
# Main Execution Loop
#==========================
async def main():
    ssid = 'Add_Your_Ssid'
    client = AsyncPocketOptionClient(ssid, is_demo=True, enable_logging=True, auto_reconnect=True)
    last_fetch = 0
    interval = 300

    while True:
        try:
            if not client.is_connected:
                logger.info(f"{bl}Connecting...{ENDC}")
                if not await client.connect():
                    logger.error(f"{error} Connection failed, retrying...{ENDC}")
                    await asyncio.sleep(10)
                    continue
                rprint(Panel(f"{OKCYAN}Connected!{ENDC}", title=f"{g}Status{ENDC}"))

            balance = await client.get_balance()
            rprint(Panel(
                f"{DARK_GRAY}Balance: {g}{balance.balance:.2f} USD{ENDC}\n"
                f"{DARK_GRAY}Demo: {ye}{balance.is_demo}{ENDC}\n"
                f"{DARK_GRAY}Uid: {g}{getattr(client, 'uid', '--')}{ENDC}",
                title=f"{PURPLE}Account Info{ENDC}"
            ))

            now = time.time()
            if now - last_fetch >= interval:
                assets = await client.get_available_assets()
                rprint(Panel(f"{ye}Open assets{ENDC}", title=f"{PURPLE}Assets{ENDC}"))
                print_assets_table(assets, only_open=True)
                last_fetch = now

            payout = await client.get_payout("EURUSD_otc", "1m")
            rprint(f"{g}Payout: {ye}{payout}%{ENDC}")
            candles_df = await client.get_candles_dataframe("EURUSD_otc", "1m", count=10)
            print_candles_table(candles_df, "EURUSD_otc", format_timeframe(60))

            # Place a test order
            logger.info("Placing test order (EURUSD_otc CALL 1$ / 1m)...")
            order_id = None
            try:
                order = await client.place_order("EURUSD_otc", amount=1.0, direction=OrderDirection.CALL, duration=60)
                order_id = order.order_id
                rprint(f"{cy}Order Placed: {ye}{order.order_id} {w}- {g}{order.status.value}{ENDC}")
            except Exception as e:
                logger.error(f"Failed to place order: {e}", exc_info=True)
                await asyncio.sleep(10)
                continue

            # Check win result in background
            if order_id:
                logger.info(f"Starting background check for win result of order {order_id}...")
                asyncio.create_task(check_win_task(client, order_id))

            # Check order result and display in CMD
            profit, status = await client.check_win(order_id)
            rprint(f"{ye}[ Trade {order_id} ] Status: {status.upper()} | Profit: ${profit:.2f}{ENDC}")

            order = await client.place_order(asset="EURUSD_otc", amount=1.0, direction=OrderDirection.PUT, duration=60)
            order_id = order.order_id
            rprint(f"{DARK_GRAY}Order placed with ID: {ye}{order_id}{ENDC}")
            profit, status = await client.check_win(order_id)
            rprint(f"{DARK_GRAY}Order result: {ye}{status.upper()}, {DARK_GRAY}Profit: {g}${profit:.2f}{ENDC}")

            # Wait before the next iteration
            logger.info("Waiting 60 seconds before next iteration...")
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"❗ Error in main loop: {e}", exc_info=True)
            logger.info("Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        except KeyboardInterrupt:
            logger.info("Stopping due to user interrupt...")
            break

if __name__ == "__main__":
    asyncio.run(main())
