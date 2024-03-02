import asyncio

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        stdout = stdout.decode('gbK')
        print(f'[stdout]\n{stdout}')
    if stderr:
        stderr = stderr.decode('gbK')
        print(f'[stderr]\n{stderr}')

if __name__ == '__main__':
    asyncio.run(run('dir C:/asda'))