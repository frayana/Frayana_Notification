#!/usr/bin/env python3
"""
Multi-Feed Viewer GUI
A graphical interface to view and browse multiple website feeds with tabs
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from xml.etree import ElementTree as ET
import webbrowser
import threading


class FeedTab:
    """Individual feed tab component"""
    def __init__(self, parent, feed_name, feed_url):
        self.parent = parent
        self.feed_name = feed_name
        self.feed_url = feed_url
        self.entries = []
        self.current_link = ""
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Create the UI for this feed tab"""
        # Top frame with URL and refresh button
        top_frame = ttk.Frame(self.frame, padding="10")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(top_frame, text="Feed URL:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.url_entry = ttk.Entry(top_frame, width=60, font=('Arial', 9))
        self.url_entry.insert(0, self.feed_url)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        self.refresh_btn = ttk.Button(top_frame, text="🔄 Refresh", command=self.fetch_feed)
        self.refresh_btn.grid(row=0, column=2, padx=5)
        
        top_frame.columnconfigure(1, weight=1)
        
        # Status bar
        self.status_label = ttk.Label(self.frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # Main content area - split into list and details
        main_frame = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)
        
        # Left panel - Entry list
        left_frame = ttk.Frame(main_frame, padding="5")
        main_frame.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Feed Entries:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.entry_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 9))
        self.entry_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.entry_listbox.yview)
        
        self.entry_listbox.bind('<<ListboxSelect>>', self.on_entry_select)
        
        # Right panel - Entry details
        right_frame = ttk.Frame(main_frame, padding="5")
        main_frame.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="Entry Details:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Title
        self.title_label = tk.Label(right_frame, text="", font=('Arial', 12, 'bold'), 
                                     wraplength=500, justify=tk.LEFT, anchor=tk.W, fg='#2c3e50')
        self.title_label.pack(fill=tk.X, pady=(0, 5))
        
        # Date
        self.date_label = tk.Label(right_frame, text="", font=('Arial', 9), 
                                    fg='#7f8c8d', anchor=tk.W)
        self.date_label.pack(fill=tk.X, pady=(0, 5))
        
        # Link button
        self.link_btn = ttk.Button(right_frame, text="🔗 Open in Browser", command=self.open_link, state=tk.DISABLED)
        self.link_btn.pack(pady=(0, 10))
        
        # Description
        ttk.Label(right_frame, text="Description:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
        
        self.description_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, 
                                                          font=('Arial', 9), height=20)
        self.description_text.pack(fill=tk.BOTH, expand=True)
        self.description_text.config(state=tk.DISABLED)
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
    
    def set_status(self, message, color='black'):
        """Update status bar"""
        self.status_label.config(text=message, foreground=color)
    
    def fetch_feed(self):
        """Fetch feed in a separate thread"""
        self.set_status("Fetching feed...", 'blue')
        self.refresh_btn.config(state=tk.DISABLED)
        
        # Run in thread to avoid freezing GUI
        thread = threading.Thread(target=self._fetch_feed_thread)
        thread.daemon = True
        thread.start()
    
    def _fetch_feed_thread(self):
        """Worker thread to fetch feed"""
        try:
            url = self.url_entry.get().strip()
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the feed
            entries = self.parse_feed(response.text)
            
            # Update GUI in main thread
            self.frame.after(0, lambda: self.display_entries(entries))
            
        except requests.exceptions.RequestException as e:
            self.frame.after(0, lambda: self.set_status(f"Error: {str(e)}", 'red'))
            self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch feed:\n{str(e)}"))
        except Exception as e:
            self.frame.after(0, lambda: self.set_status(f"Error: {str(e)}", 'red'))
            self.frame.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
        finally:
            self.frame.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL))
    
    def parse_feed(self, content):
        """Parse RSS/Atom feed content"""
        try:
            root = ET.fromstring(content)
            entries = []
            
            # Try RSS format
            items = root.findall('.//item')
            if items:
                for item in items:
                    entry = {
                        'title': item.find('title').text if item.find('title') is not None else 'No title',
                        'link': item.find('link').text if item.find('link') is not None else '',
                        'description': item.find('description').text if item.find('description') is not None else 'No description available',
                        'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else ''
                    }
                    entries.append(entry)
            else:
                # Try Atom format
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                atom_entries = root.findall('.//atom:entry', ns)
                
                if not atom_entries:
                    atom_entries = root.findall('.//entry')
                
                for entry in atom_entries:
                    title_elem = entry.find('atom:title', ns) if ns else entry.find('title')
                    link_elem = entry.find('atom:link', ns) if ns else entry.find('link')
                    summary_elem = entry.find('atom:summary', ns) if ns else entry.find('summary')
                    published_elem = entry.find('atom:published', ns) if ns else entry.find('published')
                    
                    entry_data = {
                        'title': title_elem.text if title_elem is not None else 'No title',
                        'link': link_elem.get('href', '') if link_elem is not None else '',
                        'description': summary_elem.text if summary_elem is not None else 'No description available',
                        'pubDate': published_elem.text if published_elem is not None else ''
                    }
                    entries.append(entry_data)
            
            return entries
        except ET.ParseError as e:
            raise Exception(f"Failed to parse feed XML: {str(e)}")
    
    def display_entries(self, entries):
        """Display entries in the listbox"""
        self.entries = entries
        self.entry_listbox.delete(0, tk.END)
        
        if not entries:
            self.set_status("No entries found in feed", 'orange')
            return
        
        for i, entry in enumerate(entries):
            self.entry_listbox.insert(tk.END, f"{i+1}. {entry['title']}")
        
        self.set_status(f"Loaded {len(entries)} entries", 'green')
        
        # Auto-select first entry
        if entries:
            self.entry_listbox.selection_set(0)
            self.on_entry_select(None)
    
    def on_entry_select(self, event):
        """Handle entry selection"""
        selection = self.entry_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        entry = self.entries[index]
        
        # Update details panel
        self.title_label.config(text=entry['title'])
        self.date_label.config(text=f"Published: {entry['pubDate']}" if entry['pubDate'] else "")
        
        # Update description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, entry['description'])
        self.description_text.config(state=tk.DISABLED)
        
        # Enable/update link button
        self.current_link = entry['link']
        if entry['link']:
            self.link_btn.config(state=tk.NORMAL)
        else:
            self.link_btn.config(state=tk.DISABLED)
    
    def open_link(self):
        """Open the current entry's link in browser"""
        if self.current_link:
            webbrowser.open(self.current_link)


class MultiFeedViewerGUI:
    """Main application with multiple feed tabs"""
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Feed Viewer")
        self.root.geometry("950x750")
        self.root.minsize(700, 500)
        
        # Configure feeds - add more feeds here!
        self.feeds = [
            {"name": "Soul of Fire / Layer 4", "url": "https://souloffire.weebly.com/layer-4-database-v2/feed"},
            {"name": "NeoDarkLand Networks", "url": "https://neodarkland.weebly.com/main-entrance/feed"}
        ]
        
        # Set up the GUI
        self.setup_ui()
        
        # Auto-load all feeds on startup
        self.root.after(100, self.load_all_feeds)
    
    def setup_ui(self):
        """Create the main user interface with tabs"""
        # Create notebook (tab container)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a tab for each feed
        self.feed_tabs = []
        for feed in self.feeds:
            tab = FeedTab(self.notebook, feed["name"], feed["url"])
            self.feed_tabs.append(tab)
            self.notebook.add(tab.frame, text=f"📰 {feed['name']}")
        
        # Add "Refresh All" button at the bottom
        button_frame = ttk.Frame(self.root, padding="5")
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        refresh_all_btn = ttk.Button(button_frame, text="🔄 Refresh All Feeds", 
                                      command=self.load_all_feeds, 
                                      style='Accent.TButton')
        refresh_all_btn.pack(side=tk.RIGHT, padx=5)
        
        # Info label
        info_label = ttk.Label(button_frame, 
                               text=f"Viewing {len(self.feeds)} feeds", 
                               font=('Arial', 9))
        info_label.pack(side=tk.LEFT, padx=5)
    
    def load_all_feeds(self):
        """Load all feeds at once"""
        for tab in self.feed_tabs:
            tab.fetch_feed()


def main():
    """Main function"""
    root = tk.Tk()
    app = MultiFeedViewerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
