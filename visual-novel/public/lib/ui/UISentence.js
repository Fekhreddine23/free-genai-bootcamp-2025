// This sentence will contain a large array of text objects
// that will be used to display a sentence.
// When we have words data we can then highlight words
// along with the audio the correct timing.

class UISentence extends UIItem{
    constructor(scene,options){
        super('sentence');
        this.visible = true
        this.wordWrap = options?.wordWrap || scene.cameras.main.width * 0.5; // Default to 80% of screen width if not provided
        this.wordsData = []
        this.words = [];
        this.x = null;
        this.y = null;
        this.height = 0;
        // load 100 text fields that we can recycle
        // based on target sentence
        
        const fontStyle = {
            fontFamily: 'Noto Sans JP',
            fontSize: '32px',
            color: '#ffffff'
        }

        this.normalColor = '#ffffff'
        this.highlightColor = '#FF0000'

        for (let i = 0; i < 100; i++) {
          this.words.push(scene.add.text(0, 0, '',fontStyle));
        }

        // Create a temporary text object to calculate line height
        const tempText = scene.add.text(0, 0, 'Tg', fontStyle);
        this.lineHeight = tempText.height
        this.lineHeightPlus = tempText.height * 1.2; // Use 120% of text height for line spacing
        tempText.destroy();
    }

    set(wordsData){
      this.wordsData = wordsData
      // clear existing sentence
      this.clear()
      // iterate through 
      let x = this.x || 0;
      let y = this.y || 0;
      let lineStartX = this.x || 0; // Starting position of the current line

      // if there are no words...
      if (this.wordsData.length === 0) {
        this.height = 0;
        return;
      }

      for (let i = 0; i < this.wordsData.length; i++) {
        const wordData = this.wordsData[i];
        const wordObject = this.words[i]
        wordObject.setText(wordData.word)
        wordObject.setVisible(true)
        // factor in wordWrap
        if (x > lineStartX && x + wordObject.width > this.wordWrap) {
          // Move to the next line
          x = lineStartX;
          y += this.lineHeightPlus;
        }
        wordObject.setPosition(x,y)
        x += wordObject.width
      }
      // there has to be at least one line so we add the line height
      this.height = (y + this.lineHeight) - this.y
    }

    setPosition(newX, newY) {
      this.x = newX;
      this.y = newY;

      let x = this.x || 0;
      let y = this.y || 0;
      let lineStartX = this.x || 0; // Starting position of the current line
      for (let i = 0; i < this.wordsData.length; i++) {
        const wordObject = this.words[i]
        // factor in wordWrap
        if (x > lineStartX && x + wordObject.width > this.wordWrap) {
          // Move to the next line
          x = lineStartX;
          y += this.lineHeightPlus;
        }
        wordObject.setPosition(x,y)
        x += wordObject.width
      }
      // there has to be at least one line so we add the line height
      this.height = (y + this.lineHeight) - this.y
    }

    setVisible(visible) {
      this.visible = visible
      for (let i = 0; i < this.words.length; i++) {
        this.words[i].setVisible(visible)
      }
    }
    getDimensions() {
      if (this.visible) {
        return { width: this.wordWrap, height: this.height }
      } else {
        return { width: 0, height: 0 }
      }
    }

    resetHighlighting() {
      for (let i = 0; i < this.words.length; i++) {
        this.words[i].setColor(this.normalColor);
      }
    }

    highlightWord(currentTime) {
        // Check each word's time range
        for (let i = 0; i < this.wordsData.length; i++) {
          const wordData = this.wordsData[i];
          const wordObject = this.words[i];
          
          // If current time is within this word's time range
          if (currentTime >= wordData.start && currentTime <= wordData.end) {
            wordObject.setColor(this.highlightColor);
          } else {
            wordObject.setColor(this.normalColor);
          }
        }
    }


    // iterate through and clear all words
    clear(){
      for (let i = 0; i < this.words.length; i++) {
        const word = this.words[i]
        word.setText('')
        word.setVisible(false)
      }
    }


}