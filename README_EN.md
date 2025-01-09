# Video Clip Extraction Tool Gemini

[English](README_EN.md) | [中文](README.md)

A video clip extraction tool based on Python + Gemini API + ffmpeg.

Extract video clips that match specific conditions based on prompts.

By modifying the prompts, different analysis and extraction effects can be achieved, such as shot analysis, plot analysis, character analysis, etc.

The example implements the basic functionality of extracting all clips of a specific character. (That's why I also call this tool the Fern Extractor ^ ^)

The principle is quite simple: input a video, design prompts, get JSON format timeline, and then extract video clips through ffmpeg.

This project mainly serves as practice for integrating with LLM API.

Gemini's video analysis function extracts image frames at 1 frame per second and audio at 1Kbps. Each frame input consumes 258 tokens, and each second of audio input consumes 32 tokens. Each second of video content becomes about 300 tokens, which means a 1 million token context window can only hold slightly less than an hour of video content. Reference: [Gemini Vision Technical Details](https://ai.google.dev/gemini-api/docs/vision?hl=en&lang=python#technical-details-video).

Based on current testing, Gemini's results are more accurate when analyzing 2-4 minute videos. Longer videos can be processed, but I find the responses less satisfactory. For details, please refer to [Model Test Records](model_test_record.md).

## System Requirements
- Windows 10 or higher
- Python 3.8+
- FFmpeg
- Internet access with proxy support

## Installation Steps

### 1. Install Python
- Visit [Python Official Website](https://www.python.org/downloads/) to download and install Python
- Check "Add Python to PATH" during installation

### 2. Install FFmpeg
1. Visit [FFmpeg Official Website](https://ffmpeg.org/download.html) to download Windows version
2. Extract the downloaded file
3. Add the bin directory from the extracted FFmpeg folder to system environment variables

### 3. Clone Project
```
git clone https://github.com/BunnRecord/VideoClipExtractionToolGemini.git
```

### 4. Install Dependencies
Open command prompt (CMD) in project root directory and run:
```
pip install -r requirements.txt
```

### 5. Get API Key
![Get Gemini API](GeminiAPI.png)
1. Visit [Google AI Studio](https://ai.google.dev/) and log in with Google account
2. Click "Get API key" button in left menu
3. Click "Create API key" button to get your API key
4. Copy the key and configure it in the project

Note: Please keep your API key secure and do not expose it in public code

## Usage Instructions

### 1. Basic Operations

1. Enable proxy for internet access.

2. Open `7.videoprocess.py` to configure parameters:
   - GOOGLE_API_KEY (Gemini API key)
   - SELECTED_MODEL (Choose Gemini model)
   - SEGMENT_DURATION (Video segment duration)
   - CHARACTER_IMAGE_PATH (Character reference image path)
   - CHARACTER_PROMPT (Character analysis prompt)
   - VIDEO_PROMPT (Video content analysis prompt)
   - CLIP_TIME_BUFFER (Buffer time for extracted video clips)

3. Run `python 7.videoprocess.py` in command line.

4. Select video files in the popup window.

5. The process will run automatically.

6. If an error occurs, check which Part failed and use `6.videoprocess.py` to continue processing that specific Part.

### 2. Program Flow

Check Program Flow in [Flowchart.png](FlowchartEN.png)

### 3. Program Flow Details

#### 3.1 Initialization
- Configure logging system
- Set Google API key
- Configure proxy
- Create necessary output directories

#### 3.2 Video File Selection
- Select one or multiple video files through file dialog

#### 3.3 Split Video into Parts
- Split video into parts, each about 120s (determined by SEGMENT_DURATION)

#### 3.4 Character Feature Analysis
- Upload character reference image
- Send character feature analysis request
- Get and save character analysis results

#### 3.5 Video Processing Loop
Each Part goes through:

1. **Video Compression**
   - Calculate target bitrate
   - Compress video
   - Save to `outputs/{video_name}/compressed/` directory

2. **Video Analysis**
   - Upload compressed video
   - Wait for processing
   - Send analysis request
   - Get analysis results

3. **Result Saving**
   - Create analysis report (Markdown format)
   - Save to `outputs/{video_name}/analysis/` directory

4. **JSON Processing**
   - Extract and update JSON content
   - Save to `outputs/{video_name}/splitjson/` directory

5. **Video Clip Extraction**
   - Extract video clips based on analysis results
   - Save to `outputs/{video_name}/extract/` directory

6. **JSON Merging**
   - Merge all JSON files
   - Save to `outputs/{video_name}/mergejson/` directory

### 4. Output Directory Structure

```
outputs/
└── {video_name}/
    ├── compressed/ # Compressed videos
    ├── analysis/ # Analysis reports
    ├── split/ # Split videos
    ├── splitjson/ # JSON files
    └── extract/ # Extracted video clips
```

### 5. Code Directory Structure
```
Feilun02/
├── 1.compress.py # Compress video
├── 2.split.py # Split video
├── 3.gemini_analysis.py # Video Gemini analysis (with character image)
├── 3.1gemini_analysis_single_video.py # Video Gemini analysis (single video)
├── 4.extract.py # Extract video clips based on timeline JSON
├── 5.mergejson.py # Merge JSON files
├── 6.partprocess.py # Process individual Parts
├── 7.videoprocess.py # Main program
└── component # API usage step-by-step scripts
    ├── 3.1test.py # Test API communication
    ├── ...
    ├── 3.9gemini_video_chatsession_struct.py # Gemini video analysis structured output
    ├── 3.11gemini_multi_model.py # Gemini multimodal video analysis interface
    └── 3.12gemini_multi_nointerface.py # Gemini multimodal video analysis
```

## Usage Suggestions

The Pro model provides more detailed video descriptions than the Flash model but runs slower. If you don't need highly detailed descriptions, consider using the Flash model.

Flash model occasionally might miss some clips, but generally performs well in most cases.

For more details, please refer to [Model Test Records](model_test_record.md).

Additionally, as of January 5, 2025, Google's free quota allows:
- Pro model: 50 free requests per day
- Flash model: 1,500 free requests per day

Flash model also has significantly lower costs compared to Pro.

For specific pricing, refer to Gemini's [Pricing Page](https://ai.google.dev/pricing).

```
Gemini 1.5 Flash

Input price: $0.075 per million tokens
Output price: $0.30 per million tokens
Context cache: $0.01875 per million tokens
```

A 180s video consumes approximately 50k tokens, so analyzing a 60-minute video using Gemini 1.5 Flash costs about $0.5.

```
Gemini 1.5 Pro

Input price: $12.5 per million tokens
Output price: $50.00 per million tokens
Context cache: $0.3125 per million tokens
```

A 180s video consumes approximately 50k tokens, so analyzing a 60-minute video using Gemini 1.5 Pro costs about $87.5.

While Pro provides better analysis than Flash, it's significantly more expensive. However, model rates tend to decrease over time, and with Gemini 2.0 models coming soon, there's much to look forward to.

## Common Issues
1. If you get "ffmpeg is not recognized as an internal or external command", check if FFmpeg is correctly added to environment variables
2. If dependencies are missing, verify that `pip install -r requirements.txt` was executed correctly

## Important Notes
- Ensure all installation steps are completed before first use
- Processing large files may take considerable time, please be patient
- There's a 5-second wait between processing videos to avoid API limits
- All processing logs are saved in `log/batch_Process.log`

## Technical Support
If you encounter any issues, please submit an Issue or contact the developer at ghosting0942@gmail.com.

## Gemini Reference Links

- Use Gemini online: [Google AI Studio](https://aistudio.google.com/prompts/new_chat)

- [Gemini API Reference Documentation](https://ai.google.dev/gemini-api/docs?hl=zh-cn)

- [Gemini API Pricing](https://ai.google.dev/pricing)

- [Gemini 2.0 Official Introduction](https://ai.google.dev/pricing)
