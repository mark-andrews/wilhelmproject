// The following code uses code obtained from 
// https://github.com/jonhoo/tetris-tutorial.git, db0b589, Copyright by Jon Gjengset 2014, 2105
// which is released by Creative Commons Attribution 4.0 International Public License
// https://creativecommons.org/licenses/by/4.0/legalcode
$('#show-tetris-instructions').click(
        function(){
            $('#tetris-extra-instructions').show();
        }
);

var TetrisObject = function (domtag, gatewayurl, ping_uid) {


    var self = Widget({HeadTag: $(domtag),
                       gatewayurl: gatewayurl,
                       ping_uid: ping_uid});

    self.gamebox = self.HeadTag.find('#gamebox');
    self.board_element = self.HeadTag.find('#tetris-board');
    self.gameOver = self.HeadTag.find('#GameOver');
    self.score_element = self.HeadTag.find('#score');
    self.rotate_btn = self.HeadTag.find('#rotate');
    self.move_down_btn = self.HeadTag.find('#down');
    self.move_left_btn = self.HeadTag.find('#left');
    self.move_right_btn = self.HeadTag.find('#right');
    self.countdown_box = self.HeadTag.find('#countdown-time');

    self.StimulusTag = self.gamebox;

    self.canvas = self.board_element[0];
    self.ctx = self.canvas.getContext("2d");

    self.I = [
            [
                    [0, 0, 0, 0],
                    [1, 1, 1, 1],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
            ],
            [
                    [0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0],
            ],
            [
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [1, 1, 1, 1],
                    [0, 0, 0, 0],
            ],
            [
                    [0, 1, 0, 0],
                    [0, 1, 0, 0],
                    [0, 1, 0, 0],
                    [0, 1, 0, 0],
            ]
    ];

    self.J = [
            [
                    [1, 0, 0],
                    [1, 1, 1],
                    [0, 0, 0]
            ],
            [
                    [0, 1, 1],
                    [0, 1, 0],
                    [0, 1, 0]
            ],
            [
                    [0, 0, 0],
                    [1, 1, 1],
                    [0, 0, 1]
            ],
            [
                    [0, 1, 0],
                    [0, 1, 0],
                    [1, 1, 0]
            ]
    ];

    self.L = [
            [
                    [0, 0, 1],
                    [1, 1, 1],
                    [0, 0, 0]
            ],
            [
                    [0, 1, 0],
                    [0, 1, 0],
                    [0, 1, 1]
            ],
            [
                    [0, 0, 0],
                    [1, 1, 1],
                    [1, 0, 0]
            ],
            [
                    [1, 1, 0],
                    [0, 1, 0],
                    [0, 1, 0]
            ]
    ];

    self.O = [
            [
                    [0, 0, 0, 0],
                    [0, 1, 1, 0],
                    [0, 1, 1, 0],
                    [0, 0, 0, 0],
            ]
    ];

    self.S = [
            [
                    [0, 1, 1],
                    [1, 1, 0],
                    [0, 0, 0]
            ],
            [
                    [0, 1, 0],
                    [0, 1, 1],
                    [0, 0, 1]
            ],
            [
                    [0, 0, 0],
                    [0, 1, 1],
                    [1, 1, 0]
            ],
            [
                    [1, 0, 0],
                    [1, 1, 0],
                    [0, 1, 0]
            ]
    ];

    self.T = [
            [
                    [0, 1, 0],
                    [1, 1, 1],
                    [0, 0, 0]
            ],
            [
                    [0, 1, 0],
                    [0, 1, 1],
                    [0, 1, 0]
            ],
            [
                    [0, 0, 0],
                    [1, 1, 1],
                    [0, 1, 0]
            ],
            [
                    [0, 1, 0],
                    [1, 1, 0],
                    [0, 1, 0]
            ]
    ];

    self.Z = [
            [
                    [1, 1, 0],
                    [0, 1, 1],
                    [0, 0, 0]
            ],
            [
                    [0, 0, 1],
                    [0, 1, 1],
                    [0, 1, 0]
            ],
            [
                    [0, 0, 0],
                    [1, 1, 0],
                    [0, 1, 1]
            ],
            [
                    [0, 1, 0],
                    [1, 1, 0],
                    [1, 0, 0]
            ]
    ];

    self.pieces = [
            [self.I, "cyan"],
            [self.J, "blue"],
            [self.L, "orange"],
            [self.O, "yellow"],
            [self.S, "green"],
            [self.T, "purple"],
            [self.Z, "red"]
    ];

    self.newPiece = function() {
            var p = self.pieces[parseInt(Math.random() * self.pieces.length, 10)];
            return new self.Piece(p[0], p[1]);
    }

    self.drawSquare = function(x, y) {

            self.ctx.fillRect(x * self.tilesz, y * self.tilesz, self.tilesz, self.tilesz);

            var ss = self.ctx.strokeStyle;
            self.ctx.strokeStyle = "#555";
            self.ctx.strokeRect(x * self.tilesz, y * self.tilesz, self.tilesz, self.tilesz);
            self.ctx.strokeStyle = ss;

    }

    // #######################################################
    // Start Piece definition
    // #######################################################
    self.Piece = function(patterns, color) {
            this.pattern = patterns[0];
            this.patterns = patterns;
            this.patterni = 0;

            this.color = color;

            this.x = self.width/2-parseInt(Math.ceil(this.pattern.length/2), 10);
            this.y = -2;
    }

    self.Piece.prototype.rotate = function() {
            var nudge = 0;
            var nextpat = this.patterns[(this.patterni + 1) % this.patterns.length];

            if (this._collides(0, 0, nextpat)) {
                    // Check kickback
                    nudge = this.x > self.width / 2 ? -1 : 1;
            }

            if (!this._collides(nudge, 0, nextpat)) {
                    this.undraw();
                    this.x += nudge;
                    this.patterni = (this.patterni + 1) % this.patterns.length;
                    this.pattern = this.patterns[this.patterni];
                    this.draw();
            }
    };

    self.Piece.prototype._collides = function(dx, dy, pat) {
            for (var ix = 0; ix < pat.length; ix++) {
                    for (var iy = 0; iy < pat.length; iy++) {
                            if (!pat[ix][iy]) {
                                    continue;
                            }

                            var x = this.x + ix + dx;
                            var y = this.y + iy + dy;
                            if (y >= self.height || x < 0 || x >= self.width) {
                                    return self.WALL;
                            }
                            if (y < 0) {
                                    // Ignore negative space rows
                                    continue;
                            }
                            if (self.board[y][x] !== "") {
                                    return self.BLOCK;
                            }
                    }
            }

            return 0;
    };

    self.Piece.prototype.down = function() {
            if (this._collides(0, 1, this.pattern)) {
                    this.lock();
                    self.piece = self.newPiece();
            } else {
                    this.undraw();
                    this.y++;
                    this.draw();
            }
    };

    self.Piece.prototype.moveRight = function() {
            if (!this._collides(1, 0, this.pattern)) {
                    this.undraw();
                    this.x++;
                    this.draw();
            }
    };

    self.Piece.prototype.moveLeft = function() {
            if (!this._collides(-1, 0, this.pattern)) {
                    this.undraw();
                    this.x--;
                    this.draw();
            }
    };

    self.Piece.prototype.lock = function() {
            for (var ix = 0; ix < this.pattern.length; ix++) {
                    for (var iy = 0; iy < this.pattern.length; iy++) {
                            if (!this.pattern[ix][iy]) {
                                    continue;
                            }

                            if (this.y + iy < 0) {
                                    // re-initialize
                                    self.initialize();
                                    return;
                            }

                            self.board[this.y + iy][this.x + ix] = this.color;
                    }
            }

            var nlines = 0;
            for (var y = 0; y < self.height; y++) {
                    var line = true;
                    for (var x = 0; x < self.width; x++) {
                            line = line && self.board[y][x] !== "";
                    }
                    if (line) {
                            for (var y2 = y; y2 > 1; y2--) {
                                    for (var x = 0; x < self.width; x++) {
                                            self.board[y2][x] = self.board[y2-1][x];
                                    }
                            }
                            for (var x = 0; x < self.width; x++) {
                                    self.board[0][x] = "";
                            }
                            nlines++;
                    }
            }

            if (nlines > 0) {
                    self.score += nlines;
                    self.drawBoard();
                    self.score_element.text(self.score);
            }
    };

    self.Piece.prototype._fill = function(color) {
            var fs = self.ctx.fillStyle;
            self.ctx.fillStyle = color;
            var x = this.x;
            var y = this.y;
            for (var ix = 0; ix < this.pattern.length; ix++) {
                    for (var iy = 0; iy < this.pattern.length; iy++) {
                            if (this.pattern[ix][iy]) {
                                    self.drawSquare(x + ix, y + iy);
                            }
                    }
            }
            self.ctx.fillStyle = fs;
    };

    self.Piece.prototype.undraw = function(ctx) {
            this._fill(self.clear);
    };

    self.Piece.prototype.draw = function(ctx) {
            this._fill(this.color);
    };

    // #######################################################
    // End Piece definition
    // #######################################################
    
    self.on_key_press = function(k) {
        console.log('on key press');
            if (self.done) {
                    return;
            }

            if (k == self.key_codes.rotate) {
                self.rotate();
            }

            if (k == self.key_codes.down) {
                self.move_down();
            }

            if (k == self.key_codes.left) {
                self.move_left();
            }

            if (k == self.key_codes.right) { 
                self.move_right();
            }
    }

    self.drawBoard = function() {
            var fs = self.ctx.fillStyle;
            for (var y = 0; y < self.height; y++) {
                    for (var x = 0; x < self.width; x++) {
                            self.ctx.fillStyle = self.board[y][x] || self.clear;
                            self.drawSquare(x, y, self.tilesz, self.tilesz);
                    }
            }
            self.ctx.fillStyle = fs;
    }


    self.initialize = function() {
        for (var r = 0; r < self.height; r++) {
                self.board[r] = [];
                for (var c = 0; c < self.width; c++) {
                        self.board[r][c] = "";
                }
        }
        self.drawBoard();
    }


    self.on_countdown_complete = function() {
        console.log('Countdown complete.');
        
        self.done = true;
        self.gameOver.css('z-index', 2);
        self.gameOver.text('Game over')
            .delay(3000)
            .fadeOut(1000, function() {
                 results = {score: self.score};
                 self.TerminateStimulusDisplay(results);
            });
    }

    self.countdown = function(countdown_time) {
            if (countdown_time > 0) {
                self.countdown_box.hide().text(countdown_time--)
                .fadeIn(0).delay(1000)
                .fadeOut(0, function(){self.countdown(countdown_time);});
            } else {
                self.countdown_box.text(0).show();
                self.on_countdown_complete();
            }
    }

    self.main = function() {
            var now = Date.now();
            var delta = now - self.dropStart;
            
            if (delta > self.movement_speed) {
                    self.piece.down();
                    self.dropStart = now;
            }

            if (!self.done) {
                    requestAnimationFrame(self.main);
            }
    }

    self.rotate = function() {
        self.piece.rotate();
        dropStart = Date.now();
    }

    self.move_left = function() {
        self.piece.moveLeft();
        dropStart = Date.now();
    }

    self.move_right = function() {
        self.piece.moveRight();
        dropStart = Date.now();
    }

    self.move_down = function() {
        self.piece.down();
    }

    self.lines = 0;
    self.done = false;

    self.clear = 'white';
    self.width = 10;
    self.height = 20;
    self.tilesz = 20;
    self.score = 0;

    self.canvas.width = self.width * self.tilesz;
    self.canvas.height = self.height * self.tilesz;

    self.WALL = 1;
    self.BLOCK = 2;
    self.piece = null;

    self.downI = {};
    self.board = [];

    self.key_codes = {
        down: 100,
        rotate: 114,
        left: 106,
        right: 107
    }

    // $(document).keypress(function(e) {on_key_press(e.which);});


    self.ParseJsonData = function(data) {
        self.countdown_time = parseInt(data.duration);
        self.movement_speed = parseInt(data.speed);

        self.Stimuli = [
            {
                name: 'tetris'
            }
        ]

    }

    self.UserEvents = [
        {
            listener: self.rotate_btn, 
            EventNames: 'click', 
            Handler: self.rotate
        },
        {
            listener: self.move_left_btn, 
            EventNames: 'click', 
            Handler: self.move_left
        },
        {
            listener: self.move_right_btn, 
            EventNames: 'click', 
            Handler: self.move_right
        },
        {
            listener: self.move_down_btn, 
            EventNames: 'click', 
            Handler: self.move_down
        },
        {
            listener: $(document),
            EventNames: 'keypress',
            Handler: function(e) {self.on_key_press(e.which)}
        }
    ];

    self.DisplayStimulus = function(stimulus) {

        self.gamebox.show();

        self.dropStart = Date.now();

        self.piece = self.newPiece();

        self.initialize();

        self.countdown_box.text(self.countdown_time);

        self.score_element.text(self.score);

        self.countdown(self.countdown_time);

        self.StimulusDequeue();

        self.main();

    };

    self.OnStimulusTimeOut = function() {console.log('stimulus timeout');};

    return self;

}
