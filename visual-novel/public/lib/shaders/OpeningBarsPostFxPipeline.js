class OpeningBarsPostFxPipeline extends CustomPipeline {
  constructor(game) {
    const frag = `
    #define SHADER_NAME OPENING_BARS_POST_FX

    #ifdef GL_ES
    precision mediump float;
    #endif

    uniform sampler2D uMainSampler;
    // coordinate from the vertex shader
    varying vec2 outTexCoord;
    uniform float uCutoff;

    void main() {
      float diff = uCutoff / 2.0;
      if ((outTexCoord.y <= 0.5 - diff) || (outTexCoord.y >= 0.5 + diff)) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
      } else {
        gl_FragColor = texture2D(uMainSampler, outTexCoord);
      }
    }
    `;
    super(game, frag);
    this._progress = 1;
  }
}

if (typeof window !== 'undefined') {
  window.OpeningBarsPostFxPipeline = OpeningBarsPostFxPipeline;
}