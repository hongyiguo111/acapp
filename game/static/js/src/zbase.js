// Origin that served this bundle, so the same build works in production and on a local dev server
const AC_ORIGIN = new URL(import.meta.url).origin;
const AC_WS_ORIGIN = AC_ORIGIN.replace(/^http/, "ws");

export class AcGame{
    constructor(id, AcWingOS){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.AcWingOS = AcWingOS;

        this.settings = new Settings(this);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);
        this.chatroom = new AcGameChatRoom(this);
        this.leaderboard = new AcGameLeaderboard(this);
        this.user_settings = new AcGameUserSettings(this);

        this.start();
    }

    start(){
    }
}

