// The UIMessage is the following:
// its message bubble that can have its colour set.
// it has text label who the speaker is.
// it has text for japanese dialog.
// it has text for english dialog
class UIMessage extends UIItem{
    constructor(scene,options) {
        super('message')

        this.scene = scene;
        this.validateOptions(options); 
        this.x = options.position[0];
        this.y = options.position[1];

        const width = this.scene.cameras.main.width;
        this.maxWidth = width / 2;
        this.mainText = null;
        this.mainTextWords = null;
        this.subText = null;
        this.nameText = null;
        this.create();
    }

    create() {
        this.createBubble();
        this.createNameText();
        this.createMainText();
        this.createMainTextWithHighlighting();
        this.createSubText();
        this.createPlayButton();
        this.registerEvents();
    }

    registerEvents() {
        this.scene.g.eventBus.on('ui:sentence:update-highlighting', this.updateHighlighting, this);
        this.scene.g.eventBus.on('ui:sentence:reset-highlighting', this.resetHighlighting, this);
    }

    // Update word highlighting based on current audio time
    updateHighlighting(ev) {
        const currentTime = ev.dialogAudio.seek;
        this.mainTextWithHighlighting.highlightWord(currentTime);
    }

    resetHighlighting() {
        this.mainTextWithHighlighting.resetHighlighting();
    }

    setPosition(x, y) {
        this.x = x;
        this.y = y;
        this.bubblePanel.setPosition(this.x, this.y);
    }    

    update(options){
        this.nameText.setText(options.name);
        if (options.mainText) {
            if (options.mainTextWords) {
                this.mainTextWithHighlighting.setVisible(true)
                this.mainTextWithHighlighting.set(options.mainTextWords);
                this.mainText.setText(options.mainText);
                this.mainText.setVisible(false);
            } else {
                this.mainTextWithHighlighting.setVisible(false)
                this.mainTextWithHighlighting.clear();
                this.mainText.setText(options.mainText);
                this.mainText.setVisible(true);
            }

        } else {
            this.mainText.setText('');
            this.mainText.setVisible(false);
        }
        
        // there is subText show it, if not hide it
        if (options.subText) {
            this.subText.setText(options.subText);
            this.subText.setVisible(true);
        } else {
            this.subText.setText('');
            this.subText.setVisible(false);
        }
        const audioKey = this.scene.dialogManager.dialogNode.audio
        if (audioKey) {
            this.playButton.setVisible(true)
        } else {
            this.playButton.setVisible(false)
        }
        this.bubblePanel.autoResizePanel();
    }

    createBubble() {
        this.bubblePanel = this.scene.g.ui.createPanel({
            position: [this.x, this.y],
            layout: 'vertical',
            spacing: 8,
            minWidth: 400,
            padding: 16,
            origin: [0,0],
            panelOptions: {
                backgroundImage: 'black-sq'
            }
        });
    }

    createPlayButton(){
        this.playButton = this.scene.g.ui.createPlayButton({
            position: [0,0],
            mode: 'play2stop',
            eventHandle: 'dialog-play'
        })
        this.bubblePanel.addItem(this.playButton);
    }

    createNameText() {
        this.nameText = this.scene.g.ui.createLabel({
            position: [0,0],
            text: '',
            style: {
                fontFamily: 'Arial',
                fontSize: '24px',
                color: '#ffffff'
            }
        });
        this.bubblePanel.addItem(this.nameText);
    }

    createMainText() {
        const width = this.scene.cameras.main.width * 0.8;
        this.mainText = this.scene.g.ui.createLabel({
            position: [0,0],
            text: '',
            style: {
                fontFamily: 'Noto Sans JP',
                fontSize: '32px',
                color: '#ffffff',
                wordWrap: { width: width, useAdvancedWrap: true }
            }
        });
        this.bubblePanel.addItem(this.mainText);
    }

    createMainTextWithHighlighting() {
        const width = this.scene.cameras.main.width * 0.8;
        this.mainTextWithHighlighting = new UISentence(this.scene,{
            wordWrap: width
        })
        this.bubblePanel.addItem(this.mainTextWithHighlighting);
    }

    createSubText() {
        const width = this.scene.cameras.main.width * 0.8;
        this.subText = this.scene.g.ui.createLabel({
            position: [0,0],
            text: '',
            style: {
                fontFamily: 'Arial',
                fontSize: '24px',
                color: '#808080',
                wordWrap: { width: width, useAdvancedWrap: true }
            }
        });
        this.bubblePanel.addItem(this.subText);
    }

     /**
     * Validates the options passed to the constructor
     * @param {object} options - The options to validate
     */
    validateOptions(options) {
        OptsValidator.validate(options, {
            position: { type: 'position', required: true },
            size: { type: 'size' },
            backgroundImage: { type: 'string' },
            textStyle: { type: 'object' },
            padding: { type: 'number' }
        });
    }

    getDimensions() {
        // TODO - if the item is not visible, show this return 0,0?
        // What should happen in this case?
        return this.bubblePanel.getDimensions();
    }
}

if (typeof module !== 'undefined') {  
    module.exports = UIMessage;
}