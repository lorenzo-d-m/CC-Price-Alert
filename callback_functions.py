from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackContext
)
from trader import Trader
from custom.settings import *


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback function showing bot commands"""
    print('/start')
        
    content = update.to_dict()
    text_start1 = f'Hi {content["message"]["chat"]["first_name"]}! Welcome to Cryptocurrency Price Alert.\n'
    text_start2 = 'This bot sends you a notification if a cryptocurrency overtake stop-prices.\n\nHere the command list:\n\n'
    cm = f"{' '*8}/start\n\n{' '*8}/setassetrange\n\n{' '*8}/assettrade\n\n{' '*8}/stop"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_start1+text_start2+cm)


###################################################
##################  ASSET RANGE  ##################
###################################################
# return codes for ConversationHandler asset-range
# They could be anything, here they are int.
TO_SET_ASSET_AR, TO_SET_LOWER_SP, TO_SET_UPPER_SP = range(3)

async def asset_range_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset-range ConversationHandler.
    It starts the conversation and ask user for asset id.
    Asset id is the way data-source API identifies the asset.
    """
    print('asset_range')
    
    if not context.user_data.get('ar_list'): # first time in asset-range
        context.user_data['ar_list'] = []

    await update.message.reply_text("Please, enter the CoinGecko id of the asset")
    return TO_SET_ASSET_AR


async def set_asset_get_lowersp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset-range ConversationHandler.
    It stores the asset id and ask the user for the lower stop-price.
    """
    print('set_asset_get_lowersp')

    asset_id = update.message.text.lower()
    if asset_id in [ t.get('asset_id') for t in context.user_data['ar_list'] ]:
        await update.message.reply_text(f"{asset_id} already exists.")
        return asset_range_entry_point(update=update, context=context)
    else:
        context.user_data['ar_list'].append( {'asset_id': asset_id } )
        await update.message.reply_text(f"{asset_id} set.\nPlease, enter the lower stop price ($)")
        return TO_SET_LOWER_SP


async def set_lowersp_get_uppersp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset-range ConversationHandler.
    It stores the lower stop-price and ask the user for the upper stop-price
    """
    print('set_lowersp_get_uppersp')

    lower_sp = float(update.message.text)
    context.user_data['ar_list'][-1]['lower_sp'] = lower_sp

    await update.message.reply_text(f"{lower_sp} $ set.\nPlease, enter the upper stop price ($)")
    return TO_SET_UPPER_SP


async def set_uppersp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset-range ConversationHandler.
    It stores the upper stop-price and start the background price monitoring
    """
    print('set_uppersp_start_background')

    upper_sp = float(update.message.text)
    context.user_data['ar_list'][-1]['upper_sp'] = upper_sp
    
    await update.message.reply_text(f"{upper_sp} $ set.")

    asset_id = context.user_data['ar_list'][-1]['asset_id']
    lower_sp = context.user_data['ar_list'][-1]['lower_sp'] 
    await update.message.reply_text(
        f"Check data:\n\n{' '*8}{asset_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/startfollow or /clean"
        )


async def clean_asset_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset-range ConversationHandler.
    It cleans up the last information about asset-range and 
    exits the asset-range ConversationHandler.
    """
    print('/clean_asset_range')

    context.user_data['ar_list'].pop()
    await update.message.reply_text('Last asset id, lower sp and upper sp cleaned')
    return ConversationHandler.END


async def start_follow_asset_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset-range ConversationHandler.
    It calls repeatedly the range-check function, running it in a new job, in background.
    It also exits the asset-range ConversationHandler.
    """
    print('start_follow_asset_range')

    asset_id = context.user_data['ar_list'][-1]['asset_id']
    lower_sp = context.user_data['ar_list'][-1]['lower_sp']
    upper_sp = context.user_data['ar_list'][-1]['upper_sp']

    await update.message.reply_text(
        f"Background monitoring:\n\n{' '*8}{asset_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/stopassetrange"
    )

    # To keep things separate, even if asset_id, lower_sp and upper_sp are in context.user_data, 
    # they are set inside the Trader object and passed to the auxiliary job as auxiliary data.
    # In this way, every aux_job has its own aux_data.
    trader = Trader(MAX_OLDNESS_PRICE)
    trader.asset_id = asset_id
    trader.lower_sp = lower_sp
    trader.upper_sp = upper_sp
    
    
    aux_data = {
        'update': update,
        'trader': trader,
        #'asset_id': asset_id,
        #'lower_sp': lower_sp,
        #'upper_sp': upper_sp
    }
    
    # pre-call to check asset_id
    pre_job_id = context.job_queue.run_once(
        callback=aux_job,
        when=0,
        data=aux_data,
        name=f"pre_{context.user_data['ar_list'][-1]['asset_id']}",
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
    )
    context.user_data['ar_list'][-1]['job_id'] = pre_job_id

    # run repeating in background
    job_id = context.job_queue.run_repeating(
        callback=aux_job, 
        interval=DATA_SOURCE_REQUESTS_RATE,
        #first=0,
        #last=60,
        data=aux_data, 
        name=f"{context.user_data['ar_list'][-1]['asset_id']}",
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
    )
    context.user_data['ar_list'][-1]['job_id'] = job_id
    return ConversationHandler.END


async def aux_job(context: CallbackContext):
    """
    This is a scheduled job managed by context.job_queue.
    It needs a data-source and a trader, and they determine if the asset price is or isn't into the range.
    """
    print('background_asset_range')
    
    trader = context.job.data['trader']
    asset_id = trader.asset_id
    lower_sp = trader.lower_sp
    upper_sp = trader.upper_sp

    try:
        evaluation = trader.check_price_in_range()
    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f'{e}\nStill monitoring asset-range though')
    else:
        if evaluation[0]: # price under the lower sp
            notification = f"{asset_id} {evaluation[0]} $\nUNDER THE LOWER SP {lower_sp}"
            await context.bot.send_message(chat_id=context.job.chat_id, text=notification)
            await stop_follow_asset_range(context.job.data['update'], context)
            
        if evaluation[2]: # price above the upper sp
            notification = f"{asset_id} {evaluation[2]} $\nABOVE THE UPPER SP {upper_sp}"
            await context.bot.send_message(chat_id=context.job.chat_id, text=notification)
            await stop_follow_asset_range(context.job.data['update'], context)
    


async def stop_follow_asset_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset-range.
    It stops monitoring the asset-range for the given asset id.
    If only one asset-range is set, it doesn't need the asset id.
    """
    print('stop_follow_asset_range')
    
    print('Jobs before stop request')
    context.job_queue.scheduler.print_jobs()

    if len(context.user_data['ar_list']) == 0:
        await update.message.reply_text(f"No asset-range set.")
    elif len(context.user_data['ar_list']) == 1:
        asset_id = context.user_data['ar_list'][0].get('asset_id')
        lower_sp = context.user_data['ar_list'][0].get('lower_sp')
        upper_sp = context.user_data['ar_list'][0].get('upper_sp')
        job_id = context.user_data['ar_list'][0].get('job_id')

        job_id.schedule_removal()
        context.user_data['ar_list'].pop()
        print('Jobs after stop request')
        context.job_queue.scheduler.print_jobs()
        await update.message.reply_text(
            f"Stop monitoring:\n\n{' '*8}{asset_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/setassetrange"
            )
    elif ' '.join(context.args).lower() == 'all':
        context.job_queue.scheduler.remove_all_jobs('default')
        print('Jobs after stop request')
        context.job_queue.scheduler.print_jobs()
        await update.message.reply_text(f"Stop monitoring all assets")
    else:
        asset_id = ' '.join(context.args).lower()
        for t in context.user_data['ar_list']:
            if t.get('asset_id') == asset_id:
                lower_sp = t.get('lower_sp')
                upper_sp = t.get('upper_sp')
                job_id = t.get('job_id')

                job_id.schedule_removal()
                context.user_data['ar_list'].remove(t)
                print('Jobs after stop request')
                context.job_queue.scheduler.print_jobs()
                await update.message.reply_text(
                    f"Stop monitoring:\n\n{' '*8}{asset_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/setassetrange"
                    )


async def get_active_asset_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset-range.
    It shows the active jobs monitoring assets.
    """
    print('get_active_asset_range')
    
    jobs = ''
    for j in context.job_queue.jobs():
        jobs += f'\n{j.name}'
    
    if jobs == '':
        await update.message.reply_text('No active asset-range')
    else:
        await update.message.reply_text(f'Active asset-range list:{jobs}')


###################################################
##################  ASSET STATS  ##################
###################################################
# return codes for ConversationHandler asset-range
# They could be anything, here they are int.
TO_SET_ASSET_STATS, TO_SET_DAYS = range(2)

async def asset_stats_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset statistics ConversationHandler.
    It starts the conversation and ask user for asset id.
    Asset id is the way data-source API identifies the asset.
    """
    print('asset_stats_entry_point')
    
    # if not context.user_data.get('as_list'): # first time in asset stats
    #     context.user_data['as_list'] = []
    context.user_data['asset_stats'] = {}

    await update.message.reply_text("Please, enter the CoinGecko id of the asset")
    return TO_SET_ASSET_STATS


async def set_asset_get_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for asset stats ConversationHandler.
    It stores the asset id and ask the user for the number of days to consider.
    Please note: 
    """
    print('set_asset_get_days')

    asset_id = update.message.text.lower()
    # if asset_id in [ t.get('asset_id') for t in context.user_data['ar_list'] ]:
    #     await update.message.reply_text(f"{asset_id} already exists.")
    #     return asset_range(update=update, context=context)
    # else:
    #     context.user_data['ar_list'].append( {'asset_id': asset_id } )
    #     await update.message.reply_text(f"{asset_id} set.\nPlease, enter the lower stop price ($)")
    #     return TO_SET_LOWER_SP
    
    context.user_data['asset_stats']['asset_id'] = asset_id
    await update.message.reply_text(f"{asset_id.capitalize()} set.\nPlease, enter the number of days to consider")
    return TO_SET_DAYS


async def set_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset stats ConversationHandler.
    It stores the number of days and push the recap
    """
    print('set_days')

    days = int(update.message.text)
    context.user_data['asset_stats']['days'] = days
    
    await update.message.reply_text(f"{context.user_data['asset_stats']['asset_id'].capitalize()}\n{days} days history.\n\n/getstats or /clean")


async def clean_asset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset stats ConversationHandler.
    It clears asset stats.
    """
    print('clear_asset_stats')

    context.user_data['asset_stats'] = {}
    await update.message.reply_text("Cleaned")
    return ConversationHandler.END

    
async def get_asset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for asset stats ConversationHandler.
    It pushes the resulting statistics.
    """
    print('get_asset_stats')

    trader = Trader()
    trader.asset_id = context.user_data['asset_stats']['asset_id']
    days = context.user_data['asset_stats']['days']
    stats = trader.get_avg_std(days)
    price = stats.get("price")
    max = stats.get('max')
    min = stats.get('min')
    avg = stats.get('avg')
    std = stats.get('std')
    volatility = stats.get('volatility')
    await update.message.reply_text(f"{trader.asset_id.capitalize()}, {days} days\n\nPrice: {price}\n\nMax: {max}\n\nMin: {min}\n\nAvg: {avg}\n\nStd: {std}\n\nVolatility: {volatility:.4f}")
    return ConversationHandler.END
    