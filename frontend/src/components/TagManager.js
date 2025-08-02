import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { X, Plus, Tag } from 'lucide-react';

const TagManager = ({ conversationId, currentTags = [], onTagsUpdate }) => {
  const [newTag, setNewTag] = useState('');
  const [tags, setTags] = useState(currentTags);
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  const handleAddTag = () => {
    const tag = newTag.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      const updatedTags = [...tags, tag];
      setTags(updatedTags);
      setNewTag('');
      updateTagsOnServer(updatedTags);
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    const updatedTags = tags.filter(tag => tag !== tagToRemove);
    setTags(updatedTags);
    updateTagsOnServer(updatedTags);
  };

  const updateTagsOnServer = async (updatedTags) => {
    if (!conversationId) return;
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ tags: updatedTags })
      });

      if (response.ok) {
        if (onTagsUpdate) {
          onTagsUpdate(updatedTags);
        }
      } else {
        console.error('Failed to update tags');
        // Revert on error
        setTags(currentTags);
      }
    } catch (error) {
      console.error('Error updating tags:', error);
      // Revert on error
      setTags(currentTags);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  // Predefined common tags
  const commonTags = [
    'payment', 'urgent', 'hot', 'lead', 'parent', 
    'cancellation', 'enrollment', 'grade8', 'grade9', 
    'high-school', 'elementary', 'complaint', 'compliment'
  ];

  const suggestedTags = commonTags.filter(tag => !tags.includes(tag));

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <Tag className="w-4 h-4 text-slate-600" />
        <span className="text-sm font-medium text-slate-700">Tags</span>
      </div>

      {/* Current Tags */}
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <Badge
            key={tag}
            variant="secondary"
            className="flex items-center space-x-1 px-2 py-1"
          >
            <span className="text-xs">{tag}</span>
            <button
              onClick={() => handleRemoveTag(tag)}
              className="ml-1 hover:text-red-600"
              disabled={isLoading}
            >
              <X className="w-3 h-3" />
            </button>
          </Badge>
        ))}
      </div>

      {/* Add New Tag */}
      <div className="flex space-x-2">
        <Input
          placeholder="Adicionar tag..."
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyPress={handleKeyPress}
          className="text-sm"
          disabled={isLoading}
        />
        <Button
          onClick={handleAddTag}
          size="sm"
          disabled={!newTag.trim() || isLoading}
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      {/* Suggested Tags */}
      {suggestedTags.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs text-slate-500">Tags sugeridas:</span>
          <div className="flex flex-wrap gap-1">
            {suggestedTags.slice(0, 6).map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  const updatedTags = [...tags, tag];
                  setTags(updatedTags);
                  updateTagsOnServer(updatedTags);
                }}
                className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded-full transition-colors"
                disabled={isLoading}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TagManager;