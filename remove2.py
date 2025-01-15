
def update_origin():
    import subprocess

    # Capture the output of a bash command
    branch = subprocess.run(['git', 'branch'], capture_output=True, text=True)

    # Print the output
    print(branch.stdout)
    print(type(branch.stdout), len(branch.stdout))


    lines = [
        'git add .',
        'git commit -m "auto"',
        'git push origin VM_trading'
    ]
    for line in lines:
        print("update_origin bash execution():")
        print('line:', line)
        output = subprocess.run(line.strip().split(" "), capture_output=True, text=True)
        print("output:", output.stdout)

update_origin()
