class UIPlayButton extends UIItem {
    /**
     * @param {Phaser.Scene} scene 
     * @param {object} options - Options for the play button
     * @param {string} options.eventHandle - The string that is emitted in the eventbus
     * @param {Array} options.position - [x,y] position of the button
     * @param {string} options.mode - Mode of the button: 'play2pause' or 'play2stop'
     * @param {string} [options.image] - Play button image key
     * @param {string} [options.image_pause] - Pause button image key
     * @param {string} [options.image_stop] - Stop button image key
     */
    constructor(scene, options) {
      super('play-button')
      this.validateOptions(options); // if anything fails it will throw an error

      this.x = options.position[0];
      this.y = options.position[1];

      this.scene = scene;
      this.visible = true
      
      // possible states
      // stopped - the button is ready to be played
      // playing - the button is currently playing
      // paused - the button is currently paused
      this.state = 'stopped';

      this.eventHandle = options.eventHandle || 'default';
      
      // possible modes
      // play2pause - play -> pause
      // play2stop - play -> stop
      this.mode = options.mode || 'play2pause';
    
      this.imagePlayKey = options.image || 'play-button';
      this.imagePauseKey = options.image_pause || 'pause-button';
      this.imageStopKey = options.image_stop || 'stop-button';

      this.image = this.scene.add.image(this.x, this.y, this.imagePlayKey)
      this.image.setOrigin(0, 0) // Set origin to top-left
      this.image.setInteractive({ useHandCursor: true })
      this.image.on('pointerover', this.pointerOver,this)
      this.image.on('pointerout', this.pointerOut,this)
      this.image.on('pointerdown', this.pointerDown,this)
      this.image.on('pointerup', this.pointerUp,this)
    }

    setStop() {
      this.state = 'stopped'
      this.image.setTexture(this.imagePlayKey)
    }

    pointerDown() {
      let action = null;
      if (this.mode === 'play2pause') {
        if (this.state === 'stopped') {
          this.state = 'playing'
          action = 'play'
          this.image.setTexture(this.imagePauseKey)
        } else if (this.state === 'paused') {
          this.state = 'playing'
          action = 'play'
          this.image.setTexture(this.imagePauseKey)
        } else if (this.state === 'playing') {
          this.state = 'paused'
          action = 'pause'
          this.image.setTexture(this.imagePlayKey)
        }
      } else if (this.mode === 'play2stop') {
        if (this.state === 'stopped') {
          this.state = 'playing'
          action = 'play'
          this.image.setTexture(this.imageStopKey)
        } else if (this.state === 'playing') {
          this.state = 'stopped'
          action = 'stop'
          this.image.setTexture(this.imagePlayKey)
        }
      }
      this.scene.g.eventBus.emit(`ui:play-button:${this.eventHandle}:pointerdown`, { item: this, scene: this.scene, action: action });
    }

    pointerUp() {
        this.scene.g.eventBus.emit(`ui:play-button:${this.eventHandle}:pointerup`, { item: this, scene: this.scene });
    }

    pointerOver() {
        this.scene.g.eventBus.emit(`ui:play-button:${this.eventHandle}:pointover`, { item: this, scene: this.scene });
    }

    pointerOut() {
        this.scene.g.eventBus.emit(`ui:play-button:${this.eventHandle}:pointout`, { item: this, scene: this.scene });
    }

    getDimensions() {
      if (this.visible) {
          return {
              width: this.image.width || 0,
              height: this.image.height || 0
          };
      } else {
          return {width: 0, height: 0};
      }
    }

    setVisible(visible) {
      this.visible = visible;
      this.image.setVisible(visible);
    }

    setPosition(x, y) {
        // Store the new position
        this.x = x;
        this.y = y;
        //update the positions
        this.image.x = x;
        this.image.y = y;
    }

    validateOptions(options) {
      // Use OptsValidator to validate all required options
      OptsValidator.validate(options, {
        position: { type: 'position', required: true },
        eventHandle: { type: 'string', required: true },
        mode: { 
          type: 'oneOf', 
          values: ['play2pause', 'play2stop'], 
          required: true, 
          message: 'Mode must be either "play2pause" or "play2stop"'
        },
        image: { type: 'string' },
        image_pause: { type: 'string' },
        image_stop: { type: 'string' }
      });
    }
}

if (typeof window !== 'undefined') {
  window.UIPlayButton = UIPlayButton;
}