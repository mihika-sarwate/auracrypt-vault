const { WaveFile } = require('wavefile');

function embedMessage(wavBuffer, messageStr) {
    const messageBuf = Buffer.from(messageStr, 'utf8');
    const msgLen = messageBuf.length;

    let wav = new WaveFile(wavBuffer);
    wav.toBitDepth('16'); 
    let samples = wav.getSamples(false, Int16Array); 
    
    let isStereo = samples.length > 0 && samples[0].length !== undefined;
    let flatSamples = isStereo 
        ? new Int16Array(samples[0].length * samples.length) 
        : samples;

    if (isStereo) {
        let idx = 0;
        for (let i = 0; i < samples[0].length; i++) {
            for (let ch = 0; ch < samples.length; ch++) {
                flatSamples[idx++] = samples[ch][i];
            }
        }
    }

    let totalBits = 32 + (msgLen * 8);
    if (totalBits > flatSamples.length) {
        throw new Error('Message is too large for this audio file capacity');
    }

    let sampleIdx = 0;
    
    // Embed length (32 bit signed int)
    for (let i = 0; i < 32; i++) {
        let bit = (msgLen >> i) & 1;
        flatSamples[sampleIdx] = (flatSamples[sampleIdx] & ~1) | bit;
        sampleIdx++;
    }

    // Embed message
    for (let i = 0; i < msgLen; i++) {
        let charByte = messageBuf[i];
        for(let j = 0; j < 8; j++){
            let bit = (charByte >> j) & 1;
            flatSamples[sampleIdx] = (flatSamples[sampleIdx] & ~1) | bit;
            sampleIdx++;
        }
    }

    // Repack
    if (isStereo) {
        let idx = 0;
        for (let i = 0; i < samples[0].length; i++) {
            for (let ch = 0; ch < samples.length; ch++) {
                samples[ch][i] = flatSamples[idx++];
            }
        }
        wav.fromScratch(wav.fmt.numChannels, wav.fmt.sampleRate, '16', samples);
    } else {
        wav.fromScratch(1, wav.fmt.sampleRate, '16', flatSamples);
    }

    return wav.toBuffer();
}

function extractMessage(wavBuffer) {
    let wav = new WaveFile(wavBuffer);
    wav.toBitDepth('16');
    let samples = wav.getSamples(false, Int16Array);
    
    let isStereo = samples.length > 0 && samples[0].length !== undefined;
    let flatSamples = isStereo 
        ? new Int16Array(samples[0].length * samples.length) 
        : samples;

    if (isStereo) {
        let idx = 0;
        for (let i = 0; i < samples[0].length; i++) {
            for (let ch = 0; ch < samples.length; ch++) {
                flatSamples[idx++] = samples[ch][i];
            }
        }
    }

    let sampleIdx = 0;
    let msgLen = 0;
    
    for (let i = 0; i < 32; i++) {
        let bit = flatSamples[sampleIdx] & 1;
        msgLen |= (bit << i);
        sampleIdx++;
    }

    if(msgLen <= 0 || msgLen > (flatSamples.length / 8)) {
        throw new Error('No valid message found or corrupted audio');
    }

    let msgBuf = Buffer.alloc(msgLen);
    for (let i = 0; i < msgLen; i++) {
        let charByte = 0;
        for(let j = 0; j < 8; j++){
            let bit = flatSamples[sampleIdx] & 1;
            charByte |= (bit << j);
            sampleIdx++;
        }
        msgBuf[i] = charByte;
    }

    return msgBuf.toString('utf8');
}

function generateNoiseWav(seconds = 3) {
    const sampleRate = 44100;
    const numSamples = sampleRate * seconds;
    const samples = new Int16Array(numSamples);
    
    // Generate white noise to perfectly camouflage the LSB
    for (let i = 0; i < numSamples; i++) {
        samples[i] = Math.floor(Math.random() * 65535) - 32768;
    }
    
    let wav = new WaveFile();
    wav.fromScratch(1, sampleRate, '16', samples);
    return wav.toBuffer();
}

module.exports = { embedMessage, extractMessage, generateNoiseWav };
