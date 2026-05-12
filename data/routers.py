from handlers import commands, leaderboard, profile, change_lang, tests, host_test, verify

routers_list = [
    commands.router,
    tests.router,
    leaderboard.router,
    profile.router,
    change_lang.router,
    host_test.router,
    verify.router,
]
