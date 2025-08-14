# Facebook Messenger Chatbot.

> This a V2 of [Page-bot](https://github.com/Sman12345678/Page-bot)

An intelligent Facebook Messenger chatbot built with Python, featuring automated responses, command processing, and persistent conversation memory. This bot leverages the Facebook Graph API and Flask to create an interactive messaging experience.

## 🌟 Key Features

- **Intelligent Message Processing**: Automated responses using AI
- **Command System**: Rich set of commands with customizable prefix
- **Media Handling**: Support for image processing and attachments
- **Persistent Memory**: Maintains conversation history per user
- **Admin Controls**: Built-in error reporting and monitoring
- **API Integration**: REST API endpoint for external integrations
- **Database Backed**: SQLite storage for messages and user context

## 🛠️ Technical Stack

- **Backend**: Python 3.8+
- **Framework**: Flask
- **Database**: SQLite
- **APIs**: Facebook Graph API, Facebook Messenger Platform
- **Additional Services**: Google's Generative AI

## 📋 Core Functionalities

### Message Processing
- Real-time message handling through Facebook webhooks
- Support for text and image messages
- Conversation history tracking (last 20 messages per user)
- Automated response generation

### Command System
Available commands include:
- `/help` - View all commands
- `/imagine` - Generate images
- `/mail` - Send emails
- `/lyrics` - Get song lyrics
- `/image` - Search for images
- `/bbc` - Latest news headlines
- `/report` - Send feedback to owner

### Admin Features
- Error reporting system
- Message status logging
- Uptime monitoring
- Performance analytics

## 🗄️ Data Structure

The bot uses SQLite with three main tables:
- **conversations**: Stores message history
- **user_context**: Manages user states and preferences
- **message_logs**: Tracks message delivery status

## ⚙️ Configuration

Required environment variables:
- `PAGE_ACCESS_TOKEN`: Facebook Page Access Token
- `VERIFY_TOKEN`: Webhook verification token
- `ADMIN_ID`: Facebook User ID for admin notifications
- `PREFIX`: Command prefix (default: `/`)

## 🔐 Security Features

- Secure token handling
- Webhook verification
- Request validation
- Rate limiting
- Error logging and monitoring

## 📊 API Endpoints

- `GET /webhook`: Facebook verification endpoint
- `POST /webhook`: Main webhook for Messenger events
- `GET /api`: REST API for programmatic access
- `GET /status`: Bot status and uptime information
- `GET /`: Home page

## 🚀 Performance

- Real-time message processing
- Efficient database queries
- Optimized image handling
- Scalable webhook processing

## 📝 Logging

Comprehensive logging system includes:
- Incoming requests
- Message processing
- API interactions
- Error tracking
- Performance metrics

## ⚠️ Error Handling

- Automated error reporting to admin
- Detailed error logs
- Graceful failure recovery
- User-friendly error messages

---

Created by [Suleiman](https://github.com/Sman12345678)
