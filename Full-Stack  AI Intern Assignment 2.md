## **AI-Powered Digital Asset Management**

Organizations often have large collections of images, videos, brochures and other marketing files stored across folders with unclear filenames. So, finding a particular asset becomes difficult unless someone already knows its name or location.

Build a small Digital Asset Management system that can index a collection of media files and help users find relevant assets using natural-language search.

For example:

* “A woman standing with a cat”  
* “Customer testimonial videos”  
* “Brochures related to residential projects”  
* “Images showing a modern living room”  
* “Videos containing construction activity”

We are not expecting a complete enteprise product. Focus on building the core ingestion, understanding and retrieval flow properly.

## **Dataset**

Collect a mixed media dataset of approximately **5 to 10 GB** from public usable sources.

It should contain a reasonable mix of:

* Images  
* Videos  
* PDF documents or brochures

If hardware, storage or internet limitations prevent you from collecting the full dataset, you may use a smaller dataset. Mention the limitation and explain how your solution would handle a larger collection.

## **Expected Flow**

1. Collect media files.  
2. Store the collected files in a local folder and configure your application to process that folder.  
3. The application scans and indexes supported files.  
4. Useful metadata and AI-generated information are stored.  
5. The user searches using a natural-language prompt.  
6. The application returns the most relevant assets.  
7. The user can preview the result and locate the original file.

## **Minimum Requirements**

The solution should demonstrate:

* Ingestion of images, videos and PDF files  
* Extraction of basic metadata such as filename, type, size and location  
* AI-based understanding of file content  
* Natural language or semantic search  
* Search results ranked by relevance  
* Preview of images and supported documents  
* Filters for file type and other useful metadata  
* Indexing progress and processing status  
* Clear handling of unsupported or failed files  
* Avoiding duplicate indexing  
* Re-running indexing without processing every unchanged file again  
* Persistent storage of indexed information  
* A simple and usable search interface

For videos, you do not need to process every frame. Decide on a reasonable approach and explain it.

The search should use the actual content of the assets. A solution based only on filenames, folder names or manually entered tags will not be sufficient.

## **Search Evaluation**

Create at least 10 test searches for your dataset.

For each search, mention:

* What the user is trying to find  
* Which assets you expect to appear  
* Whether the returned results are relevant  
* Any cases where the search performs poorly

We want to understand how you checked the quality of your solution, not only whether the search API returns a response.

## **Reliability**

Your solution should consider:

* Large folders that take time to process  
* While indexing it should be reliable(because we are processing huge data)  
* Corrupted or unsupported files  
* Duplicate files in different folders  
* AI or model-processing failure

You may decide how much of this you implement and how much you explain, but the core indexing and search flow must work.

## **Technical Freedom**

You may choose your own:

* Frontend and backend stack  
* Database or vector store  
* AI models  
* Embedding approach  
* Video-processing method  
* Local or cloud-based processing  
* System architecture

Paid infrastructure is not required. Open-source models and local databases may be used.

Things i am not expecting: Design, authentication system, user management and cloud deployment(run it locally).

## **What to Submit**

* Source-code repository  
* Clear setup and run instructions  
* Sample environment file without secrets  
* Short architecture and data-flow explanation  
* Dataset summary, including total size and file counts  
* Search evaluation results  
* Short demo video showing ingestion and different searches  
* Known limitations and production improvements

Do not upload the full media dataset to the repository.

The project should run using the instructions provided in the repository.

## **Evaluation**

We will mainly evaluate:

* Whether the complete flow works  
* Quality and relevance of search results  
* Approach to images, videos and documents  
* Ability to handle a reasonably large dataset  
* Backend and data-design decisions  
* Failure handling and incremental indexing  
* Usability of the search experience  
* Ability to explain and modify the solution

The size of the dataset alone will not determine the score. We are more interested in how the system is designed and how well it works.

## **Time**

Submission deadline: **mentioned on email**

Build the most complete working solution you can within the available time. Clearly mention anything you could not complete and how you would approach it next.

