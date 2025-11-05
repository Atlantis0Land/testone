Documentation for the asynchronous API.

### 1\. Submit Transcription Task

This request uploads the audio file and queues it for processing. It returns a `task_id` immediately so the client does not have to wait.

**Request:**

```bash
curl -X POST "https://ai.dhr.gov.om/transcribe" \
     -H "X-API-Key: your_secret_key_here_12345" \
     -F "file=@test.mp3"
```

**Immediate Response:**
The server confirms the task is queued and provides its ID.

```json
{"task_id":"98024abb-327b-48b9-bfab-894be24d1f2c","status":"pending"}
```

-----

### 2\. Retrieve Task Result

Use the `task_id` from Step 1 to poll this endpoint. Check it repeatedly until the `status` is no longer "pending".

**Request:**

```bash
curl -X GET "https://ai.dhr.gov.om/status/98024abb-327b-48b9-bfab-894be24d1f2c" \
     -H "X-API-Key: your_secret_key_here_12345"
```

**Final Response (When Completed):**
When the task is done, the API returns the "completed" status and the transcription results.

```json
{"status":"completed","full_text":"لايزال استكشاف كوكب المريخ في بدايته","segments":[{"id":0,"seek":0,"start":0.0,"end":10.72,"text":"لايزال استكشاف كوكب المريخ في بدايته","tokens":[50364,8717,5016,1863,11778,25957,6055,4587,1211,4032,9566,15040,5172,7578,15844,264,935,50900],"temperature":1.0,"avg_logprob":-3.3238475197239925,"compression_ratio":0.8620689655172413,"no_speech_prob":0.08584459871053696}]}
```

-----

### Why Use Two Separate Requests?

This is an **asynchronous (non-blocking) pattern**, required for tasks that take a long time.

  * **Problem:** Audio transcription is slow (can take seconds or minutes). A single HTTP request that waits for it to finish will **time out** and fail.
  * **Solution:**
    1.  **POST (Step 1):** The first request is very fast. It only accepts the file and puts it in a queue (like the `asyncio.Queue` in your code). It returns a `task_id` immediately.
    2.  **GET (Step 2):** The client can "poll" (check) this status endpoint. This is a separate, fast request to see if the background worker has finished the job.

**Advantage:** This prevents HTTP timeouts, frees the client, and allows the server to handle many long-running jobs at once.
