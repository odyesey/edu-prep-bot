from handlers import (commands, leaderboard,
                      profile, change_lang,
                      verify, tests,
                      host_test, resources)

routers_list = [
    commands.router,
    tests.router,
    leaderboard.router,
    profile.router,
    change_lang.router,
    verify.router,
    host_test.router,
    resources.router,
]
