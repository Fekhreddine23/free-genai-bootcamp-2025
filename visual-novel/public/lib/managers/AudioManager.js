/**
 * AudioManager.js
 * Handles background music and sound effects
 */
class AudioManager {
    constructor(globalManagers) {
        this.g = globalManagers;
        this.scene = null; // Initialize scene to null
        this.bgMusic = null;
        this.sfxAudios = {};
        this.voiceAudios = {};
        this.soundEffects = {
            click: null,
            transition: null
        };
    }

    create(){
        this.createBgm();
        this.createSfxAudios();
    }


    getDialog(sceneId,voiceKey){
        const key = `dialog-${sceneId}-${voiceKey}`
        return this.voiceAudios[key];
    }

    createDialog(dialogKeys){
        this.voiceAudios = {};
        const volume = this.g.settings.get('voiceVolume');
        for (const dialogKey of dialogKeys) {
            let audio = this.scene.sound.add(dialogKey,{volume});
            this.voiceAudios[dialogKey] = audio;
        }
    }

    createSfxAudios () {
        try {
            for (const audioAsset of window.audioAssets) {
                const volume = this.g.settings.get('sfxVolume');
                this.sfxAudios[audioAsset.id] = this.scene.sound.add(audioAsset.id, {
                    volume
                });
            }
        } catch (error) {
            console.error('Error setting up sound effects:', error);
        }
    }

    createBgm () {
        try {
            const volume = this.g.settings.get('bgmVolume');
            this.bgMusic = this.scene.sound.add('bg-music', {
                volume,
                loop: true
            });

        } catch (error) {
            console.error('Error setting up background music:', error);
        }
    }
    
    
    /**
     * Update the scene reference
     * @param {Phaser.Scene} scene - The new scene
     */
    updateScene(scene) {
        this.scene = scene;
    }
    
    playSoundEffect(key, config = {}) {
        try {
            const volume = this.g.settings.get('sfxVolume');
            
            // Play the sound effect
            this.sfxAudios[key].play({
                volume,
                ...config
            });
        } catch (error) {
            console.warn(`Error playing sound effect ${key}:`, error);
        }
    }
    
    playDialog(sceneId,voiceKey) {
        const key = `dialog-${sceneId}-${voiceKey}`
        try {
            const volume = this.g.settings.get('voiceVolume');
            this.voiceAudios[key].play({
                volume,
                loop: false
            });
        } catch (error) {
            console.warn(`Error playing sound effect ${key}:`, error);
        }
    }

    stopDialog(sceneId,voiceKey) {
        const key = `dialog-${sceneId}-${voiceKey}`
        try {
            this.voiceAudios[key].stop();
        } catch (error) {
            console.warn(`Error stopping sound effect ${key}:`, error);
        }
    }
    
    playBgm () {
        const volume = this.g.settings.get('bgmVolume');
        if (this.bgMusic && !this.bgMusic.isPlaying) {
            // Start with volume at 0
            this.bgMusic.setVolume(0);
            this.bgMusic.play();
            
            // Create a proxy object for the tween to modify
            const volumeControl = { value: 0 };
            
            this.scene.tweens.add({
                targets: volumeControl,
                value: volume,
                duration: 2500,
                onUpdate: () => {
                    // Update the actual volume on each tween step
                    this.bgMusic.setVolume(volumeControl.value);
                },
                onComplete: () => { 
                    // Ensure final volume is set correctly
                    this.bgMusic.setVolume(volume);
                }
            });
        }
    }

    stopBgm(onAfterComplete) {
        if (this.bgMusic && this.bgMusic.isPlaying) {
            // Create a proxy object for the tween to modify
            const volumeControl = { value: this.bgMusic.volume };
            console.log(volumeControl)
            
            this.scene.tweens.add({
                targets: volumeControl,
                value: 0,  // Fade to silence
                duration: 2500,  // Match your fade-in duration or adjust as needed
                onUpdate: () => {
                    // Update the actual volume on each tween step
                    this.bgMusic.setVolume(volumeControl.value);
                },
                onComplete: () => { 
                    this.bgMusic.stop();
                    console.log('done bgstop');
                    onAfterComplete()
                }
            });
        }
    }
    
    pauseBgm() {
        if (this.bgMusic && this.bgMusic.isPlaying) {
            this.bgMusic.pause();
        }
    }
    
    resumeBgm() {
        if (this.bgMusic && this.bgMusic.isPaused) {
            this.bgMusic.resume();
        }
    }
    
    setBgmVolume(volume) {
        const adjustedVolume = Math.max(0, Math.min(1, volume));
        this.bgMusic.setVolume(adjustedVolume);
    }
    
    setSfxVolume(volume) {
        const adjustedVolume = Math.max(0, Math.min(1, volume));
        for (const audioAsset of window.audioAssets) {
            this.sfxAudios[audioAsset.id].setVolume(adjustedVolume);
        }
    }

    setVoiceVolume(volume){
        const adjustedVolume = Math.max(0, Math.min(1, volume));
        //this.voiceSound.setVolume(adjustedVolume);

    }
}

// Export for use in other files
if (typeof module !== 'undefined') {
    module.exports = AudioManager;
}