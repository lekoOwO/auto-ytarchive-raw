import const

if const.CHAT_COMPRESS == "brotli":
    import brotli
    import tempfile
elif const.CHAT_COMPRESS == "zstd":
    import zstandard
    import tempfile

if const.CHAT_COMPRESS == "brotli":
    def compress_file(file):
        with open(file, encoding="utf8") as f:
            compressor = brotli.Compressor(mode=brotli.BrotliEncoderMode.TEXT)
            with tempfile.NamedTemporaryFile(prefix=(os.path.basename(file)+"."), suffix=".br", delete=False) as l:
                for line in f:
                    data = line.encode()
                    data = compressor.compress(data)
                    l.write(compressor.flush())
                l.write(compressor.finish())
                return l.name
elif const.CHAT_COMPRESS == "zstd":
    def compress_file(file):
        cctx = zstandard.ZstdCompressor()
        with open(file, "rb") as ifh, tempfile.NamedTemporaryFile(prefix=(os.path.basename(file)+"."), suffix=".zst", delete=False) as ofh:
            cctx.copy_stream(ifh, ofh)
            return ofh.name