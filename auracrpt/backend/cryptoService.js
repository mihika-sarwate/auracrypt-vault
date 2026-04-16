const crypto = require('crypto');

function generateKeyPair() {
    return crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: {
            type: 'spki',
            format: 'pem'
        },
        privateKeyEncoding: {
            type: 'pkcs8',
            format: 'pem'
        }
    });
}

function encryptMessage(publicKey, message) {
    const bufferMessage = Buffer.from(message, 'utf8');
    const encrypted = crypto.publicEncrypt({
        key: publicKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256'
    }, bufferMessage);
    return encrypted.toString('base64');
}

function decryptMessage(privateKey, encryptedBase64) {
    const bufferEncrypted = Buffer.from(encryptedBase64, 'base64');
    const decrypted = crypto.privateDecrypt({
        key: privateKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256'
    }, bufferEncrypted);
    return decrypted.toString('utf8');
}

module.exports = { generateKeyPair, encryptMessage, decryptMessage };
