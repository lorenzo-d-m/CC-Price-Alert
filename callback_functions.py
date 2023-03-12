from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackContext
)
from trader import Trader
from data_sources import CoinGeckoDataSource
from custom.settings import *


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback function showing bot commands"""
    print('/start')
        
    content = update.to_dict()
    text_start1 = f'Hi {content["message"]["chat"]["first_name"]}! Welcome to Cryptocurrency Price Alert.\n'
    text_start2 = 'This bot sends you a notification if a cryptocurrency overtake stop-prices.\n\nHere the command list:\n\n'
    cm = f"{' '*8}/start\n\n{' '*8}/tokenrange\n\n{' '*8}/tokentrade\n\n{' '*8}/stop"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_start1+text_start2+cm)


# return codes for ConversationHandler token range
# They could be anything, here they are int.
TO_SET_TOKEN, TO_SET_LOWER_SP, TO_SET_UPPER_SP, TOKEN_UPPER_SP_SET = range(4)

async def token_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It starts the conversation and ask user for token id.
    Token id is the way data-source API identifies the token.
    """
    print('token_range')
    
    if not context.user_data.get('tr_list'): # first time in token range
        context.user_data['tr_list'] = []

    await update.message.reply_text("Please, enter the CoinGecko id of the token")
    return TO_SET_TOKEN


async def set_token_get_lowersp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It stores the token id and ask the user for the lower stop-price.
    """
    print('set_token_get_lowersp')

    token_id = update.message.text.lower()
    if token_id in [ t.get('token_id') for t in context.user_data['tr_list'] ]:
        await update.message.reply_text(f"{token_id} already exists.")
        return token_range(update=update, context=context)
    else:
        context.user_data['tr_list'].append( {'token_id': token_id } )
        await update.message.reply_text(f"{token_id} set.\nPlease, enter the lower stop price ($)")
        return TO_SET_LOWER_SP


async def set_lowersp_get_uppersp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It stores the lower stop-price and ask the user for the upper stop-price
    """
    print('set_lowersp_get_uppersp')

    lower_sp = float(update.message.text)
    context.user_data['tr_list'][-1]['lower_sp'] = lower_sp

    await update.message.reply_text(f"{lower_sp} $ set.\nPlease, enter the upper stop price ($)")
    return TO_SET_UPPER_SP


async def set_uppersp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It stores the upper stop-price and start the background price monitoring
    """
    print('set_uppersp_start_background')

    upper_sp = float(update.message.text)
    context.user_data['tr_list'][-1]['upper_sp'] = upper_sp
    
    await update.message.reply_text(f"{upper_sp} $ set.")

    token_id = context.user_data['tr_list'][-1]['token_id']
    lower_sp = context.user_data['tr_list'][-1]['lower_sp'] 
    await update.message.reply_text(
        f"Check data:\n\n{' '*8}{token_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/startfollow or /clean"
        )


async def clean_token_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It cleans up the last information about token-range and 
    exits the token-range ConversationHandler.
    """
    print('/clean_token_range')

    context.user_data['tr_list'].pop()
    await update.message.reply_text('Last token id, lower sp and upper sp cleaned')
    return ConversationHandler.END


async def start_follow_token_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback function for token-range ConversationHandler.
    It calls repeatedly the range-check function, running it in a new job, in background.
    It also exits the token-range ConversationHandler.
    """
    print('start_follow_token_range')

    token_id = context.user_data['tr_list'][-1]['token_id']
    lower_sp = context.user_data['tr_list'][-1]['lower_sp']
    upper_sp = context.user_data['tr_list'][-1]['upper_sp']

    await update.message.reply_text(
        f"Background monitoring:\n\n{' '*8}{token_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/stoptokenrange"
    )

    # To keep things separate, even if token_id, lower_sp and upper_sp are in context.user_data, 
    # they are passed to the auxiliary job as auxiliary data.
    # In this way, every aux_job has its own aux_data.
    aux_data = {
        'update': update,
        'token_id': token_id,
        'lower_sp': lower_sp,
        'upper_sp': upper_sp
    }
    
    job_name = context.user_data['tr_list'][-1]['token_id']
    job_id = context.job_queue.run_repeating(
                                callback=aux_job, 
                                interval=DATA_SOURCE_REQUESTS_RATE,
                                #first=0,
                                #last=60,
                                data=aux_data, 
                                name=job_name, # is the token_id 
                                user_id=update.effective_user.id,
                                chat_id=update.effective_chat.id,
                                )
    context.user_data['tr_list'][-1]['job_id'] = job_id
    return ConversationHandler.END


async def aux_job(context: CallbackContext):
    """
    This is a scheduled job managed by context.job_queue.
    It needs a data-source and a trader, and they determine if the token price is or isn't into the range.
    """
    print('background_token_range')
    
    trader = Trader(CoinGeckoDataSource(), MAX_OLDNESS_PRICE)
    token_id = context.job.data['token_id']
    lower_sp = context.job.data['lower_sp']
    upper_sp = context.job.data['upper_sp']

    try:
        evaluation = trader.check_price_in_range(
            token_id=token_id,
            lower_sp=lower_sp,
            upper_sp=upper_sp
            )
        print('evaluation:', evaluation)
    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f'{e}\nStill monitoring token range though')
    else:
        if evaluation[0]: # price under the lower sp
            notification = f"{token_id} {evaluation[0]} $\nUNDER THE LOWER SP {lower_sp}"
            await context.bot.send_message(chat_id=context.job.chat_id, text=notification)
            return await stop_follow_token_range(context.job.data['update'], context)
            
        if evaluation[2]: # price above the upper sp
            notification = f"{'token_id'} {evaluation[2]} $\nABOVE THE UPPER SP {lower_sp}"
            await context.bot.send_message(chat_id=context.job.chat_id, text=notification)
            return await stop_follow_token_range(context.job.data['update'], context)
    


async def stop_follow_token_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for token-range.
    It stops monitoring the token-range for the given token id.
    If only one token-range is set, it doesn't need the token id.
    """
    print('stop_follow_token_range')
    
    print('Jobs before stop request')
    context.job_queue.scheduler.print_jobs()
    if len(context.user_data['tr_list']) == 0:
        await update.message.reply_text(f"No token-range set.")
    if len(context.user_data['tr_list']) == 1:
        print('len 1')
        token_id = context.user_data['tr_list'][0].get('token_id')
        lower_sp = context.user_data['tr_list'][0].get('lower_sp')
        upper_sp = context.user_data['tr_list'][0].get('upper_sp')
        job_id = context.user_data['tr_list'][0].get('job_id')

        job_id.schedule_removal()
        context.user_data['tr_list'].pop()
        print('Jobs after stop request')
        context.job_queue.scheduler.print_jobs()
        await update.message.reply_text(
            f"Stop monitoring:\n\n{' '*8}{token_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/tokenrange"
            )
    else:
        print('len long')
        token_id = ' '.join(context.args).lower()
        for t in context.user_data['tr_list']:
            if t.get('token_id') == token_id:
                lower_sp = t.get('lower_sp')
                upper_sp = t.get('upper_sp')
                job_id = t.get('job_id')

                job_id.schedule_removal()
                context.user_data['tr_list'].remove(t)
                print('Jobs after stop request')
                context.job_queue.scheduler.print_jobs()
                await update.message.reply_text(
                    f"Stop monitoring:\n\n{' '*8}{token_id}\n\n{' '*8}{lower_sp} $\n\n{' '*8}{upper_sp} $\n\n/tokenrange"
                    )


async def get_active_token_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function for token-range.
    It shows the active jobs monitoring tokens.
    """
    print('get_active_token_range')
    
    jobs = ''
    for j in context.job_queue.jobs():
        jobs += f'\n{j.name}'
    
    if jobs == '':
        await update.message.reply_text('No active token range')
    else:
        await update.message.reply_text(f'Active token range list:{jobs}')
