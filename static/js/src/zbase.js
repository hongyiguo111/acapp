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

