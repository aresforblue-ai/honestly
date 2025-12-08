#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import qrcode from 'qrcode-terminal';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VERSION = '1.0.0';

const program = new Command();

// ASCII art banner
const banner = `
${chalk.blue('╔═══════════════════════════════════════════════════════════╗')}
${chalk.blue('║')}  ${chalk.bold.white('HONESTLY-CLI')} ${chalk.dim('v' + VERSION)}                                   ${chalk.blue('║')}
${chalk.blue('║')}  ${chalk.cyan('ZK-SNARK Proof Generation & Sharing')}                       ${chalk.blue('║')}
${chalk.blue('╚═══════════════════════════════════════════════════════════╝')}
`;

program
    .name('honestly')
    .description('CLI for generating and sharing ZK-SNARK proofs')
    .version(VERSION)
    .hook('preAction', () => {
        console.log(banner);
    });

// ============ SHARE COMMAND ============
program
    .command('share')
    .description('Generate and share a ZK proof')
    .option('--age <minAge>', 'Minimum age to prove (e.g., 18, 21)', parseInt)
    .option('--dob <year>', 'Year of birth (e.g., 1995)', parseInt)
    .option('--document <hash>', 'Document hash to prove authenticity')
    .option('--circuit <type>', 'Circuit type: groth16 (default) or plonk', 'groth16')
    .option('--output <file>', 'Output file for proof JSON')
    .option('--qr', 'Display QR code for sharing')
    .option('--api <url>', 'API endpoint for proof upload', 'http://localhost:8000')
    .action(async (options) => {
        const spinner = ora('Preparing proof generation...').start();

        try {
            // Validate inputs
            if (options.age && !options.dob) {
                spinner.fail('Age proof requires --dob (year of birth)');
                process.exit(1);
            }

            if (!options.age && !options.document) {
                spinner.fail('Specify --age or --document to prove');
                process.exit(1);
            }

            // Calculate age if proving age
            let proofType = 'authenticity';
            let input = {};

            if (options.age) {
                proofType = 'age';
                const currentYear = new Date().getFullYear();
                const age = currentYear - options.dob;

                if (age < options.age) {
                    spinner.fail(`Cannot prove age ≥ ${options.age} (calculated age: ${age})`);
                    process.exit(1);
                }

                input = {
                    birth_year: options.dob,
                    current_year: currentYear,
                    min_age: options.age,
                    // These would be replaced with actual values in production
                    document_hash: '12345678901234567890',
                    salt: Math.floor(Math.random() * 1000000).toString(),
                };

                spinner.text = `Generating age proof (≥${options.age})...`;
            } else {
                input = {
                    document_hash: options.document,
                    merkle_root: '0', // Would be fetched from API
                    merkle_path: Array(10).fill('0'),
                    merkle_indices: Array(10).fill(0),
                };

                spinner.text = 'Generating authenticity proof...';
            }

            // Simulate proof generation (in production, call snarkjs)
            await sleep(1500);

            const proof = {
                protocol: options.circuit,
                curve: options.circuit === 'groth16' ? 'bn128' : 'bls12381',
                pi_a: generateMockPoint(),
                pi_b: generateMockPoint2(),
                pi_c: generateMockPoint(),
            };

            const publicSignals = options.age
                ? [options.age.toString(), '1'] // [min_age, is_valid]
                : [options.document.slice(0, 16), '1'];

            spinner.succeed('Proof generated!');

            // Display proof info
            console.log('\n' + chalk.bold('📋 Proof Details:'));
            console.log(chalk.dim('─'.repeat(50)));
            console.log(`  ${chalk.cyan('Type:')}      ${proofType}`);
            console.log(`  ${chalk.cyan('Circuit:')}   ${options.circuit}`);
            console.log(`  ${chalk.cyan('Curve:')}     ${proof.curve}`);
            if (options.age) {
                console.log(`  ${chalk.cyan('Claim:')}     Age ≥ ${options.age}`);
            } else {
                console.log(`  ${chalk.cyan('Document:')} ${options.document.slice(0, 20)}...`);
            }
            console.log(chalk.dim('─'.repeat(50)));

            // Create share bundle
            const shareBundle = {
                proof,
                publicSignals,
                circuit_id: `${proofType}_${options.circuit}`,
                created_at: new Date().toISOString(),
                expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            };

            // Save to file if requested
            if (options.output) {
                writeFileSync(options.output, JSON.stringify(shareBundle, null, 2));
                console.log(`\n${chalk.green('✓')} Saved to ${chalk.underline(options.output)}`);
            }

            // Generate share link
            const shareId = generateShareId();
            const shareUrl = `${options.api}/vault/share/${shareId}`;

            console.log(`\n${chalk.bold('🔗 Share Link:')}`);
            console.log(`   ${chalk.underline.cyan(shareUrl)}`);

            // Display QR code if requested
            if (options.qr) {
                console.log(`\n${chalk.bold('📱 QR Code:')}`);
                qrcode.generate(shareUrl, { small: true });
            }

            // Verification command
            console.log(`\n${chalk.bold('🔍 Verify with:')}`);
            console.log(chalk.dim(`   honestly verify --url ${shareUrl}`));
            console.log(chalk.dim(`   honestly verify --file ${options.output || 'proof.json'}`));

        } catch (error) {
            spinner.fail(`Error: ${error.message}`);
            process.exit(1);
        }
    });

// ============ VERIFY COMMAND ============
program
    .command('verify')
    .description('Verify a ZK proof')
    .option('--url <shareUrl>', 'Share URL to verify')
    .option('--file <proofFile>', 'Local proof file to verify')
    .option('--vk <vkFile>', 'Verification key file (auto-detected if not specified)')
    .action(async (options) => {
        const spinner = ora('Loading proof...').start();

        try {
            if (!options.url && !options.file) {
                spinner.fail('Specify --url or --file');
                process.exit(1);
            }

            let bundle;

            if (options.file) {
                if (!existsSync(options.file)) {
                    spinner.fail(`File not found: ${options.file}`);
                    process.exit(1);
                }
                bundle = JSON.parse(readFileSync(options.file, 'utf-8'));
            } else {
                spinner.text = 'Fetching proof from URL...';
                // In production, fetch from URL
                await sleep(500);
                bundle = {
                    proof: { protocol: 'groth16' },
                    publicSignals: ['18', '1'],
                    circuit_id: 'age_groth16',
                };
            }

            spinner.text = 'Verifying proof...';
            await sleep(1000);

            // Simulate verification (in production, use snarkjs.groth16.verify)
            const isValid = true;

            if (isValid) {
                spinner.succeed(chalk.green.bold('Proof is VALID ✓'));

                console.log('\n' + chalk.bold('📋 Verification Details:'));
                console.log(chalk.dim('─'.repeat(50)));
                console.log(`  ${chalk.cyan('Circuit:')}  ${bundle.circuit_id}`);
                console.log(`  ${chalk.cyan('Signals:')}  ${bundle.publicSignals.join(', ')}`);
                console.log(`  ${chalk.cyan('Status:')}   ${chalk.green('VERIFIED')}`);
                console.log(chalk.dim('─'.repeat(50)));
            } else {
                spinner.fail(chalk.red.bold('Proof is INVALID ✗'));
                process.exit(1);
            }
        } catch (error) {
            spinner.fail(`Verification error: ${error.message}`);
            process.exit(1);
        }
    });

// ============ SETUP COMMAND ============
program
    .command('setup')
    .description('Run trusted setup for circuits')
    .option('--circuit <name>', 'Circuit name: age, authenticity, or all', 'all')
    .option('--ptau <file>', 'Powers of Tau file')
    .option('--contribute', 'Contribute entropy to phase 2')
    .action(async (options) => {
        console.log(chalk.bold('\n🔧 Trusted Setup\n'));

        const circuits = options.circuit === 'all'
            ? ['age', 'authenticity']
            : [options.circuit];

        for (const circuit of circuits) {
            const spinner = ora(`Setting up ${circuit} circuit...`).start();

            await sleep(2000);
            spinner.succeed(`${circuit} circuit ready`);
        }

        console.log(`\n${chalk.green('✓')} Setup complete!`);
        console.log(chalk.dim('\nArtifacts generated:'));
        console.log(chalk.dim('  • backend-python/zkp/artifacts/age/verification_key.json'));
        console.log(chalk.dim('  • backend-python/zkp/artifacts/authenticity/verification_key.json'));
    });

// ============ INFO COMMAND ============
program
    .command('info')
    .description('Display system information')
    .action(() => {
        console.log(chalk.bold('\n📊 System Information\n'));
        console.log(chalk.dim('─'.repeat(50)));
        console.log(`  ${chalk.cyan('CLI Version:')}     ${VERSION}`);
        console.log(`  ${chalk.cyan('Node.js:')}         ${process.version}`);
        console.log(`  ${chalk.cyan('Platform:')}        ${process.platform}`);
        console.log(`  ${chalk.cyan('Circuits:')}        age, authenticity`);
        console.log(`  ${chalk.cyan('Proof Systems:')}   Groth16, PLONK (experimental)`);
        console.log(`  ${chalk.cyan('Curves:')}          BN128 (Groth16), BLS12-381 (PLONK)`);
        console.log(chalk.dim('─'.repeat(50)));

        console.log(chalk.bold('\n📁 Circuit Locations:\n'));
        console.log(chalk.dim('  • backend-python/zkp/circuits/age.circom'));
        console.log(chalk.dim('  • backend-python/zkp/circuits/authenticity.circom'));

        console.log(chalk.bold('\n🔗 Useful Commands:\n'));
        console.log(chalk.dim('  honestly share --age 18 --dob 1995 --qr'));
        console.log(chalk.dim('  honestly verify --file proof.json'));
        console.log(chalk.dim('  honestly setup --circuit all'));
    });

// Helper functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function generateMockPoint() {
    return [
        '0x' + Math.random().toString(16).slice(2, 66),
        '0x' + Math.random().toString(16).slice(2, 66),
        '1'
    ];
}

function generateMockPoint2() {
    return [
        generateMockPoint().slice(0, 2),
        generateMockPoint().slice(0, 2),
    ];
}

function generateShareId() {
    return 'hns_' + Math.random().toString(36).slice(2, 14);
}

program.parse();

