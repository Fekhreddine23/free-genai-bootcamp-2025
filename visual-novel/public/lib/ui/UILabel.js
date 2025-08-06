class UILabel extends UIItem{
    /**
     * Create a text label for UI components
     * @param {Phaser.Scene} scene - The Phaser scene
     * @param {object} options - Options for the label
     * @param {string} options.text - Text content of the label
     * @param {Array<number>} options.position - [x,y] position of the label
     * @param {object} options.style - Text style for the label (optional)
     */
    constructor(scene, options) {
        super('label')
        this.scene = scene;
        this.validateOptions(options);
        
        this.field = options.field;
        this.text = options.text || ''; // Default to empty string if no text provided
        this.x = options.position[0];
        this.y = options.position[1];
        
        // Default style if not provided
        this.style = options.style || {
            fontFamily: 'Arial',
            fontSize: '24px',
            color: '#ffffff'
        };
        
        // Create the label text
        this.createLabel();
    }
    
    /**
     * Create the text label
     */
    createLabel() {
        this.labelText = this.scene.add.text(
            this.x,
            this.y,
            this.text,
            this.style,
        );
        this.labelText.setOrigin(0,0)
    }
    
    /**
     * Set new text for the label
     * @param {string} text - New text content
     */
    setText(text) {
        this.text = text;
        this.labelText.setText(text);
    }
    
    /**
     * Set a new position for the label
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     */
    setPosition(x, y) {
        this.x = x;
        this.y = y;
        this.labelText.setPosition(x, y);
    }
    
    /**
     * Set a new style for the label
     * @param {object} style - New text style
     */
    setStyle(style) {
        this.style = style;
        this.labelText.setStyle(style);
    }
    
    /**
     * Get the label's text object
     * @returns {Phaser.GameObjects.Text} The text object
     */
    getTextObject() {
        return this.labelText;
    }
    
    /**
     * Set visibility of this label
     * @param {boolean} visible - Whether the label should be visible
     * @returns {UILabel} - This label instance for chaining
     */
    setVisible(visible) {
        this.labelText.setVisible(visible);
    }
    
    
    /**
     * Destroy the label
     */
    destroy() {
        this.labelText.destroy();
    }

    getDimensions() {
        if (this.labelText.visible === false){
            return { width: 0, height: 0 };
        } else {
            return {
                width: this.labelText.displayWidth || 0,
                height: this.labelText.displayHeight || 0
            };
        }
    }
    /**
     * Validate the options passed to the constructor
     * @param {object} options - The options object
     */
     /**
     * Validates the options passed to the constructor
     * @param {object} options - The options to validate
     */
    validateOptions(options) {
        OptsValidator.validate(options, {
            text: { type: 'string' },
            position: { type: 'position', required: true },
            style: { type: 'object' },
            origin: { type: 'array' },
            depth: { type: 'number' },
            visible: { type: 'boolean' }
        });
    }
}

if (typeof window !== 'undefined') {
    window.UILabel = UILabel;
}