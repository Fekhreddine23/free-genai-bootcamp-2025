class CustomPipeline extends Phaser.Renderer.WebGL.Pipelines.PostFXPipeline {
  constructor(game, fragShader) {
    super({
      game,
      fragShader,
    });
    this._progress = 0;
  }
  
  get progress() {
    return this._progress;
  }
  
  set progress(val) {
    this._progress = val;
  }
  
  onPreRender() {
    this.set1f('uCutoff', this._progress);
  }
}

// Export for use in other files
if (typeof module !== 'undefined') {
  module.exports = CustomPipeline;
}