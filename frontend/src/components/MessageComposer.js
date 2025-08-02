import React, { useState, useRef } from 'react';
import EmojiPicker from 'emoji-picker-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { 
  Send, 
  Paperclip, 
  Smile, 
  Mic, 
  Image, 
  FileText,
  X,
  Play,
  Pause
} from 'lucide-react';

const MessageComposer = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordingIntervalRef = useRef(null);

  const handleEmojiClick = (emojiObject) => {
    setMessage(prev => prev + emojiObject.emoji);
  };

  const handleSend = async () => {
    if (!message.trim() && !selectedFile && !audioBlob) return;

    try {
      if (selectedFile) {
        // Handle file upload
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('caption', message);
        
        await onSendMessage({
          type: selectedFile.type.startsWith('image/') ? 'image' : 'document',
          body: message || `📎 ${selectedFile.name}`,
          file: selectedFile
        });
        
        setSelectedFile(null);
      } else if (audioBlob) {
        // Handle audio message
        await onSendMessage({
          type: 'audio',
          body: '🎤 Mensagem de áudio',
          file: audioBlob
        });
        
        setAudioBlob(null);
      } else {
        // Handle text message
        await onSendMessage({
          type: 'text',
          body: message
        });
      }
      
      setMessage('');
      setShowEmojiPicker(false);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const audioChunks = [];
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Erro ao acessar o microfone. Verifique as permissões.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(recordingIntervalRef.current);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white border-t border-slate-200 p-4">
      {/* File Preview */}
      {selectedFile && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {selectedFile.type.startsWith('image/') ? (
              <Image className="w-5 h-5 text-blue-600" />
            ) : (
              <FileText className="w-5 h-5 text-blue-600" />
            )}
            <div>
              <p className="text-sm font-medium text-blue-900">{selectedFile.name}</p>
              <p className="text-xs text-blue-700">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedFile(null)}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Audio Preview */}
      {audioBlob && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Mic className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-green-900">Mensagem de áudio</p>
              <p className="text-xs text-green-700">{formatTime(recordingTime)}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAudioBlob(null)}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Recording Status */}
      {isRecording && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-red-900">
              Gravando... {formatTime(recordingTime)}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={stopRecording}
            className="text-red-600 border-red-200 hover:bg-red-50"
          >
            Parar
          </Button>
        </div>
      )}

      {/* Main Input Area */}
      <div className="flex items-end space-x-2">
        {/* Attachment Buttons */}
        <div className="flex space-x-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => imageInputRef.current?.click()}
            disabled={disabled}
            title="Enviar imagem"
          >
            <Image className="w-4 h-4" />
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            title="Enviar arquivo"
          >
            <Paperclip className="w-4 h-4" />
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={disabled}
            title={isRecording ? "Parar gravação" : "Gravar áudio"}
            className={isRecording ? "text-red-600" : ""}
          >
            <Mic className="w-4 h-4" />
          </Button>
        </div>

        {/* Message Input */}
        <div className="flex-1 relative">
          <Input
            placeholder="Digite sua mensagem..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={disabled}
            className="pr-10"
          />
          
          {/* Emoji Button */}
          <div className="absolute right-2 top-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowEmojiPicker(!showEmojiPicker)}
              disabled={disabled}
            >
              <Smile className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Send Button */}
        <Button
          onClick={handleSend}
          disabled={disabled || (!message.trim() && !selectedFile && !audioBlob)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      {/* Emoji Picker */}
      {showEmojiPicker && (
        <div className="absolute right-4 bottom-20 z-50">
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowEmojiPicker(false)}
              className="absolute -top-2 -right-2 z-10 w-6 h-6 p-0"
            >
              <X className="w-3 h-3" />
            </Button>
            <EmojiPicker
              onEmojiClick={handleEmojiClick}
              width={300}
              height={400}
            />
          </div>
        </div>
      )}

      {/* Hidden File Inputs */}
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.xlsx,.xls"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default MessageComposer;