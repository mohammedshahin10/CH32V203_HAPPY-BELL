#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mp3dec.h"

#define READBUF_SIZE (16 * 1024)

#ifdef HELIX_HOST_GRANULE_HOOK
static unsigned long hookBefore;
static unsigned long hookAfter;

static int CountGranule(void *context, int granule, short *output,
                        int outputSamps, int event)
{
    (void)context;
    if (granule < 0 || granule >= MAX_NGRAN || !output || outputSamps <= 0)
        return -1;
    if (event == MP3_GRANULE_OUTPUT_BEFORE)
        hookBefore++;
    else if (event == MP3_GRANULE_OUTPUT_AFTER)
        hookAfter++;
    else
        return -1;
    return 0;
}
#endif

int main(int argc, char **argv)
{
    unsigned char readBuf[READBUF_SIZE];
    const unsigned char *readPtr = readBuf;
    short outBuf[MAX_NCHAN * MAX_NGRAN * MAX_NSAMP];
    size_t bytesLeft = 0;
    size_t nRead;
    FILE *input;
    FILE *output;
    HMP3Decoder decoder;
    MP3FrameInfo info;
    unsigned long frames = 0;
    unsigned long samples = 0;
    int eof = 0;
    int sync;
    int result;

    if (argc != 3) {
        fprintf(stderr, "usage: helix_host_decode input.mp3 output.pcm\n");
        return 2;
    }
    input = fopen(argv[1], "rb");
    output = fopen(argv[2], "wb");
    if (!input || !output)
        return 3;
    decoder = MP3InitDecoder();
    if (!decoder)
        return 4;

    while (!eof || bytesLeft != 0) {
        if (!eof && bytesLeft < (2U * MAINBUF_SIZE)) {
            memmove(readBuf, readPtr, bytesLeft);
            nRead = fread(readBuf + bytesLeft, 1, READBUF_SIZE - bytesLeft,
                          input);
            bytesLeft += nRead;
            readPtr = readBuf;
            if (nRead == 0)
                eof = 1;
        }
        sync = MP3FindSyncWord(readPtr, (int)bytesLeft);
        if (sync < 0)
            break;
        readPtr += sync;
        bytesLeft -= (size_t)sync;
#ifdef HELIX_HOST_GRANULE_HOOK
        result = MP3DecodeWithGranuleHook(decoder, &readPtr, &bytesLeft,
                                          outBuf, 0, CountGranule, NULL);
#else
        result = MP3Decode(decoder, &readPtr, &bytesLeft, outBuf, 0);
#endif
        if (result == ERR_MP3_MAINDATA_UNDERFLOW)
            continue;
        if (result == ERR_MP3_INDATA_UNDERFLOW && !eof)
            continue;
        if (result != 0) {
            fprintf(stderr, "decode error %d after frame %lu\n", result,
                    frames);
            break;
        }
        MP3GetLastFrameInfo(decoder, &info);
        fwrite(outBuf, sizeof(short), (size_t)info.outputSamps, output);
        frames++;
        samples += (unsigned long)info.outputSamps;
    }
    MP3GetLastFrameInfo(decoder, &info);
    fprintf(stderr, "frames=%lu samples=%lu rate=%d chans=%d\n", frames,
            samples, info.samprate, info.nChans);
#ifdef HELIX_HOST_GRANULE_HOOK
    fprintf(stderr, "hook_before=%lu hook_after=%lu\n", hookBefore, hookAfter);
#endif
    MP3FreeDecoder(decoder);
    fclose(output);
    fclose(input);
    return 0;
}
