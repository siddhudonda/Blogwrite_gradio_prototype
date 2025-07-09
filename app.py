import os
import gradio as gr
import google.generativeai as genai
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Load Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Get Google Images
def get_images(query, num=3):
    """Fetch images from Google using SerpAPI"""
    if not SERPAPI_KEY:
        return []
    
    params = {
        "engine": "google",
        "q": query,
        "tbm": "isch",
        "api_key": SERPAPI_KEY,
        "num": num
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        images = []

        if "images_results" in results:
            for item in results["images_results"][:num]:
                if "original" in item:
                    images.append(item["original"])

        return images
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []

# Inject image URLs into blog text
def inject_images(text, image_urls):
    """Inject images into blog content at strategic positions"""
    if not image_urls:
        return text
    
    paragraphs = text.split('\n\n')
    result = []
    img_idx = 0

    for i, para in enumerate(paragraphs):
        result.append(para)
        # Insert image after every 2-3 paragraphs, but not immediately after title
        if i > 0 and (i + 1) % 3 == 0 and img_idx < len(image_urls):
            result.append(f"\n![Related Image]({image_urls[img_idx]})\n")
            img_idx += 1

    return '\n\n'.join(result)

# Main function
def generate_blog(topic, include_images=True, word_count="Medium (500-800 words)"):
    """Generate blog post with optional images"""
    
    if not topic.strip():
        return "⚠️ Please enter a blog topic!"
    
    # Map word count selection to prompt instruction
    word_count_map = {
        "Short (300-500 words)": "Keep it concise, around 300-500 words.",
        "Medium (500-800 words)": "Write a comprehensive post of 500-800 words.",
        "Long (800-1200 words)": "Create a detailed, in-depth post of 800-1200 words."
    }
    
    word_instruction = word_count_map.get(word_count, "Write a comprehensive post of 500-800 words.")
    
    prompt = f"""Write a well-structured, SEO-optimized blog post on the topic: "{topic}". 

Requirements:
- {word_instruction}
- Include an engaging title
- Write a compelling introduction
- Use relevant subheadings (H2/H3) for better structure
- Include a strong conclusion
- Add a call-to-action at the end
- Write in a conversational yet professional tone
- Avoid bullet points in the main content
- Return in clean markdown format

Topic: {topic}"""

    try:
        # Generate blog content
        response = model.generate_content(prompt)
        blog_text = response.text
        
        # Add images if requested
        if include_images:
            image_urls = get_images(topic, num=3)
            if image_urls:
                blog_text = inject_images(blog_text, image_urls)
                status_msg = f"✅ Blog generated successfully with {len(image_urls)} images!"
            else:
                status_msg = "✅ Blog generated successfully (no images found)"
        else:
            status_msg = "✅ Blog generated successfully (images disabled)"
        
        return blog_text, status_msg
        
    except Exception as e:
        error_msg = f"❌ Error generating blog: {str(e)}"
        return error_msg, error_msg

# Create Gradio interface
def create_interface():
    with gr.Blocks(
        title="AutoBlog Writer with Gemini + Google Images",
        theme=gr.themes.Soft()
    ) as demo:
        
        gr.Markdown("""
        # 📝 AutoBlog Writer
        ### Generate SEO-optimized blog posts with AI-powered content and relevant images
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                topic_input = gr.Textbox(
                    label="📰 Blog Topic",
                    placeholder="Enter your blog topic (e.g., 'Benefits of Remote Work', 'AI in Healthcare')",
                    lines=2
                )
                
                with gr.Row():
                    include_images = gr.Checkbox(
                        label="🖼️ Include Images",
                        value=True,
                        info="Automatically fetch and include relevant images"
                    )
                    
                    word_count = gr.Dropdown(
                        choices=[
                            "Short (300-500 words)",
                            "Medium (500-800 words)",
                            "Long (800-1200 words)"
                        ],
                        value="Medium (500-800 words)",
                        label="📏 Word Count",
                        info="Choose your preferred blog length"
                    )
                
                generate_btn = gr.Button(
                    "🚀 Generate Blog Post",
                    variant="primary",
                    size="lg"
                )
                
                status_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    show_label=False
                )
            
            with gr.Column(scale=3):
                blog_output = gr.Markdown(
                    label="Generated Blog Post",
                    height=600
                )
        
        # Event handlers
        generate_btn.click(
            fn=generate_blog,
            inputs=[topic_input, include_images, word_count],
            outputs=[blog_output, status_output]
        )
        
        # Add some example topics
        gr.Markdown("""
        ### 💡 Example Topics:
        - "The Future of Artificial Intelligence in Education"
        - "10 Proven Strategies for Digital Marketing Success"
        - "Sustainable Living: Simple Changes for a Better Planet"
        - "Remote Work Productivity: Tools and Techniques"
        """)
    
    return demo

# Launch the application
if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860
    )