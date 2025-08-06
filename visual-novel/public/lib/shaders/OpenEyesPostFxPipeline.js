class OpenEyesPostFxPipeline extends Phaser.Renderer.WebGL.Pipelines.PostFXPipeline {
    constructor(game) {
      const fragShader = `
  #define SHADER_NAME OPEN_EYES_TRANSITION
  #ifdef GL_ES
  precision highp float;
  #endif
  
  uniform sampler2D uMainSampler;
  varying vec2 outTexCoord;
  
  // Controls the eye opening (0.0 = closed, 1.0 = fully open)
  uniform float uOpenAmount;
  
  // Controls content blur amount (larger = more blur)
  uniform float uBlurAmount;
  
  // Controls edge blur/feathering (larger = more feathered edges)
  uniform float uEdgeBlurAmount;
  
  // Aspect ratio correction
  uniform vec2 uResolution;
  
  // Simple blur function for the content
  vec4 blur(sampler2D image, vec2 uv, float amount) {
      vec4 color = vec4(0.0);
      float total = 0.0;
      
      // Sample points for a simple radial blur
      for (float x = -2.0; x <= 2.0; x += 1.0) {
          for (float y = -2.0; y <= 2.0; y += 1.0) {
              vec2 offset = vec2(x, y) * amount;
              color += texture2D(image, uv + offset);
              total += 1.0;
          }
      }
      
      return color / total;
  }
  
  // Function to create a soft edge with strong feathering
  float softEllipse(vec2 uv, vec2 center, vec2 radius, float edgeWidth) {
      // Distance from center, normalized by radius
      vec2 fromCenter = (uv - center) / radius;
      
      // Distance calculation for ellipse
      float dist = length(fromCenter);
      
      // Create a soft edge
      // 1.0 = inside, 0.0 = outside, with a gradient in between
      return 1.0 - smoothstep(1.0 - edgeWidth, 1.0 + edgeWidth, dist);
  }
  
  void main() {
      // Center of screen
      vec2 center = vec2(0.5, 0.5);
      vec2 uv = outTexCoord;
      
      // Adjust aspect ratio
      float aspect = uResolution.x / uResolution.y;
      
      // Get eye dimensions
      // Width is constant and very wide
      // Height increases as eye opens
      vec2 eyeRadius = vec2(
          1.8,                            // Always wide enough to exceed screen
          max(0.001, uOpenAmount * 0.52)   // Height based on open amount
      );
      
      // Calculate edge width - automatically fade out as the eye opens
      // This makes the edge blur/feathering decrease to zero as the eye fully opens
      float dynamicEdgeWidth = uEdgeBlurAmount * (1.0 - uOpenAmount);
      
      // Get the soft edge value (1 inside, 0 outside, gradient in between)
      float eyeMask = softEllipse(vec2(uv.x, uv.y), center, eyeRadius, dynamicEdgeWidth);
      
      // Calculate content blur based on eye openness
      float contentBlur = uBlurAmount * (1.0 - uOpenAmount);
      
      // Sample the main texture with blur for inside the eye
      vec4 blurredImage = blur(uMainSampler, uv, contentBlur);
      vec4 regularImage = texture2D(uMainSampler, uv);
      
      // Mix between blurred and regular image based on eye opening
      vec4 insideColor = mix(blurredImage, regularImage, uOpenAmount);
      
      // Edge glow color - bluish when closed, whiter as it opens
      vec3 glowColor = mix(
          vec3(0.2, 0.3, 0.5),  // Blue-ish when closed
          vec3(0.6, 0.6, 0.6),  // Lighter as it opens
          uOpenAmount
      );
      
      // Edge glow intensity - stronger at the edge, fades away
      // Also decrease as the eye opens
      float edgeIntensity = 0.8 * (1.0 - eyeMask) * smoothstep(0.0, 0.3, eyeMask) * (1.0 - uOpenAmount * 0.7);
      vec4 edgeColor = vec4(glowColor * edgeIntensity, 1.0);
      
      // Outside color (black)
      vec4 outsideColor = vec4(0.0, 0.0, 0.0, 1.0);
      
      // Mix between inside content, edge glow, and outside black
      // First mix the edge and outside based on the mask edge
      vec4 finalColor;
      
      if (eyeMask > 0.99) {
          // Fully inside the eye
          finalColor = insideColor;
      } else if (eyeMask < 0.01) {
          // Fully outside the eye
          finalColor = outsideColor;
      } else {
          // At the edge - apply glow
          // Calculate strength based on distance from edge
          float edgeStrength = smoothstep(0.01, 0.99, eyeMask);
          
          // Blend between outside, glow, and inside
          if (edgeStrength < 0.5) {
              // Closer to outside - blend outside and glow
              float t = edgeStrength * 2.0;
              finalColor = mix(outsideColor, edgeColor, t);
          } else {
              // Closer to inside - blend glow and inside
              float t = (edgeStrength - 0.5) * 2.0;
              finalColor = mix(edgeColor, insideColor, t);
          }
      }
      
      gl_FragColor = finalColor;
  }
      `;
  
      // Initialize with the correct uniform list
      super({
        game: game,
        name: 'OpenEyesPostFx',
        fragShader,
        uniforms: [
          'uMainSampler',
          'uOpenAmount',
          'uBlurAmount',
          'uEdgeBlurAmount',
          'uResolution'
        ]
      });
  
      // Initialize state - store values but don't set uniforms yet
      this._openAmount = 0;         // Start with eyes closed (0 = closed, 1 = open)
      this._blurAmount = 0.018;     // Default blur amount
      this._edgeBlurAmount = 0.2;   // Default edge blur/feathering (0.2 is moderate)
      this._isBooted = false;       // Track if the pipeline has been booted
    }
  
    // Called when the pipeline is added to the renderer
    onBoot() {
      this._isBooted = true;
      
      // Set initial resolution and uniform values
      this.set2f('uResolution', this.renderer.width, this.renderer.height);
      this.set1f('uOpenAmount', this._openAmount);
      this.set1f('uBlurAmount', this._blurAmount);
      this.set1f('uEdgeBlurAmount', this._edgeBlurAmount);
    }
  
    // Method to get the current open amount (for tweening)
    get openAmount() {
      return this._openAmount;
    }
    
    // Method to set the open amount (for tweening)
    set openAmount(value) {
      this._openAmount = Phaser.Math.Clamp(value, 0, 1);
      if (this._isBooted) {
        this.set1f('uOpenAmount', this._openAmount);
      }
    }
  
    // Method to get the current blur amount (for tweening)
    get blurAmount() {
      return this._blurAmount;
    }
    
    // Method to set the blur amount (for tweening)
    set blurAmount(value) {
      this._blurAmount = value;
      if (this._isBooted) {
        this.set1f('uBlurAmount', this._blurAmount);
      }
    }
  
    // Method to get the current edge blur amount (for tweening)
    get edgeBlurAmount() {
      return this._edgeBlurAmount;
    }
    
    // Method to set the edge blur amount (for tweening)
    set edgeBlurAmount(value) {
      this._edgeBlurAmount = Phaser.Math.Clamp(value, 0.01, 1.0);
      if (this._isBooted) {
        this.set1f('uEdgeBlurAmount', this._edgeBlurAmount);
      }
    }
  
    // Called before rendering
    onPreRender() {
      if (!this._isBooted) return;
      
      // Update the resolution in case the game size changed
      this.set2f('uResolution', this.renderer.width, this.renderer.height);
    }
  }
  
  // Register the pipeline with Phaser
  if (typeof window !== 'undefined') {
    // Make the class available globally
    window.OpenEyesPostFxPipeline = OpenEyesPostFxPipeline;
  }
  
  /* 
  // Example usage with tweens:
  
  // In your scene:
  
  // 1. First register the pipeline
  this.game.renderer.pipelines.addPostPipeline('OpenEyesPostFx', OpenEyesPostFxPipeline);
  
  // 2. Apply it to a camera
  this.cameras.main.setPostPipeline(OpenEyesPostFxPipeline);
  
  // 3. Get a reference to control it
  const eyesFX = this.cameras.main.getPostPipeline(OpenEyesPostFxPipeline);
  
  // 4. Create a tween to animate the opening
  this.tweens.add({
      targets: eyesFX,
      openAmount: 1,             // Animate from 0 (current) to 1 (fully open)
      duration: 2000,
      ease: 'Cubic.easeOut',     // Use any easing function
      onComplete: () => {
          console.log('Eye opening animation complete');
      }
  });
  */