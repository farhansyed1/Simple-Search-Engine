import { useState } from 'react'
import './App.css'

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [totalResults, setTotalResults] = useState(0)
  const [hasSearched, setHasSearched] = useState(false)
  const [lastSearchedQuery, setLastSearchedQuery] = useState('')
  const [expandedParentLinks, setExpandedParentLinks] = useState({})
  const [expandedChildLinks, setExpandedChildLinks] = useState({})
  
  const handleSearch = async (query = searchQuery) => {
    if (!query.trim()) {
      setSearchError('Please enter a search query')
      return
    }
    
    try {
      setSearchLoading(true)
      setSearchResults([])
      setSearchError('')
      setHasSearched(true)
      setLastSearchedQuery(query)
    
      const response = await fetch('http://127.0.0.1:3001/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: query
        }),
      })
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json()
      
      if (data.error) {
        setSearchError(`Search error: ${data.error}`)
      } else {
        setSearchResults(data.results || [])
        setTotalResults(data.total_results || 0)
      }
    } catch (err) {
      setSearchError('Failed to execute search. Make sure the server is running.')
      console.error('Error executing search:', err)
    } finally {
      setSearchLoading(false)
    }
  }
  
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(searchQuery)
    }
  }
  
  const handleSearchButtonClick = () => {
    handleSearch(searchQuery)
  }
  
  const toggleParentLinks = (resultId) => {
    setExpandedParentLinks(prev => ({
      ...prev,
      [resultId]: !prev[resultId]
    }))
  }
  
  const toggleChildLinks = (resultId) => {
    setExpandedChildLinks(prev => ({
      ...prev,
      [resultId]: !prev[resultId]
    }))
  }

  return (
    <div className="app-container">
      <h1>Web Search Engine</h1>
      
      <div className="search-container">
        <div className="search-box">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (e.target.value === '') {
                setHasSearched(false);
                setLastSearchedQuery('');
              }
            }}
            onKeyPress={handleSearchKeyPress}
            placeholder="Enter your search query... (use quotes for phrases, e.g., 'hong kong')"
            className="search-input"
          />
          <button 
            onClick={handleSearchButtonClick} 
            className="search-button"
            disabled={searchLoading}
          >
            {searchLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
            {searchError && <div className="error-message">{searchError}</div>}
            
            {searchLoading && (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Searching...</p>
              </div>
            )}
            
        {searchResults.length > 0 && (
          <div className="search-results">
            <h2>Search Results</h2>
            <p className="search-stats">
              {totalResults > searchResults.length 
                ? `Showing top ${searchResults.length} results` 
                : `Found ${searchResults.length} results`}
            </p>
            <div className="results-list">
              {searchResults.map((result, index) => (
                  <div key={index} className="result-item">
                    <div className="search-result-formatted">
                      <div className="result-score-title">
                        <span className="result-score">{result.score.toFixed(4)}</span>
                        <span className="result-title-text">{result.title}</span>
                      </div>
                      
                      <div className="result-url-line">
                        <a href={result.url} target="_blank" rel="noopener noreferrer">{result.url}</a>
                      </div>
                      
                      <div className="result-metadata">
                        <span>{result.last_modified || 'Unknown'}</span>
                        <span className="size-separator">•</span>
                        <span>{result.size || 0} bytes</span>
                      </div>
                      
                      <div className="result-keywords-line">
                        {result.keywords && result.keywords.length > 0
                          ? result.keywords.map((k, i) => (
                              <span key={i} className="keyword-item">
                                {k.word} <span className="keyword-freq">{k.frequency}</span>
                                {i < result.keywords.length - 1 && <span className="keyword-separator">;</span>}
                              </span>
                            ))
                          : <span className="no-keywords">No keywords available</span>
                        }
                      </div>
                      
                      {result.parent_links && result.parent_links.length > 0 && (
                        <div className="result-parent-links">
                          <div className="links-title">Parent Links:</div>
                          {(expandedParentLinks[result.id] 
                            ? result.parent_links 
                            : result.parent_links.slice(0, 5)
                          ).map((link, i) => (
                            <div key={i} className="parent-link">
                              <a href={link} target="_blank" rel="noopener noreferrer">{link}</a>
                            </div>
                          ))}
                          {result.parent_links.length > 5 && (
                            <button 
                              className="see-all-button"
                              onClick={() => toggleParentLinks(result.id)}
                            >
                              {expandedParentLinks[result.id] 
                                ? 'Show Less' 
                                : `See All (${result.parent_links.length})`}
                            </button>
                          )}
                        </div>
                      )}
                                            
                      {result.child_links && result.child_links.length > 0 && (
                        <div className="result-child-links">
                          <div className="links-title">Child Links:</div>
                          {(expandedChildLinks[result.id] 
                            ? result.child_links 
                            : result.child_links.slice(0, 5)
                          ).map((link, i) => (
                            <div key={i} className="child-link">
                              <a href={link} target="_blank" rel="noopener noreferrer">{link}</a>
                            </div>
                          ))}
                          {result.child_links.length > 5 && (
                            <button 
                              className="see-all-button"
                              onClick={() => toggleChildLinks(result.id)}
                            >
                              {expandedChildLinks[result.id] 
                                ? 'Show Less' 
                                : `See All (${result.child_links.length})`}
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
              ))}
            </div>
          </div>
        )}
        
        {hasSearched && !searchLoading && searchResults.length === 0 && !searchError && (
          <div className="no-results">
            <p>No results found for "{lastSearchedQuery}"</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
