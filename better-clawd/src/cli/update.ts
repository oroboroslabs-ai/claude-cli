import chalk from 'chalk'
import { PRODUCT_NAME, PRODUCT_URL } from 'src/constants/product.js'
import { gracefulShutdown } from 'src/utils/gracefulShutdown.js'
import { writeToStdout } from 'src/utils/process.js'

export async function update() {
  writeToStdout(`Current version: ${MACRO.VERSION}\n`)
  writeToStdout('\n')
  writeToStdout(
    chalk.yellow(
      `${PRODUCT_NAME} no longer uses the upstream Anthropic auto-update service.\n`,
    ),
  )
  writeToStdout(
    'Install new builds manually from the project releases or by reinstalling from the Oroboros-Anthropic Claude CLI repository.\n',
  )
  writeToStdout('\n')
  writeToStdout(`Project: ${PRODUCT_URL}\n`)
  writeToStdout(`Releases: ${PRODUCT_URL}/releases\n`)
  await gracefulShutdown(0)
}
